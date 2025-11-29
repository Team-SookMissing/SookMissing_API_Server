from fastapi import FastAPI, HTTPException
from .core.database import get_db_conn
import httpx, logging
from .schemas.schemas import AnalyzeRequest, AnalyzeResponse
from .core.config import settings
from .utils.utils import extract_urls
from pydantic import ValidationError

app = FastAPI(title = "SookMissing API Server")
logger = logging.getLogger(__name__)

async def exists_in_blacklist(url: str) -> bool:
    conn = await get_db_conn()

    async with conn.cursor() as cur:
        await cur.execute("SELECT COUNT(*) FROM bad_urls WHERE url=%s", (url,))
        (count,) = await cur.fetchone()
        
    conn.close() 
    return count > 0


async def call_analyzer(sender_number: str, text: str) -> AnalyzeResponse:
    payload = {
        "text": text,
        "sender_number": sender_number
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            logger.info("분석 엔진 호출 시작")
            res = await client.post(settings.ANALYZER_URL, json=payload)
            logger.info(f"분석엔진 status={res.status_code}, body={res.text}")
            res.raise_for_status()

            data = res.json()
            logger.info(f"분석 엔진으로부터 받은 데이터: {data}")

            return AnalyzeResponse(**data)

        except httpx.HTTPStatusError as e:
            # 응답은 왔는데 4xx/5xx일 때
            logger.error(
                f"[Analyzer] HTTPStatusError: status={e.response.status_code}, body={e.response.text}"
            )
            raise HTTPException(
                status_code=502,
                detail=f"분석 엔진 HTTP 상태 에러: {e.response.status_code}",
            )

        except httpx.RequestError as e:
            # DNS, 연결 거부, 타임아웃 등 '요청 자체'가 실패
            logger.error(f"[Analyzer] RequestError (연결 문제): {repr(e)}")
            raise HTTPException(
                status_code=502,
                detail=f"분석 엔진 서버에 연결할 수 없습니다: {e}",
            )

        except ValidationError as e:
            logger.error(f"[Analyzer] 응답 스키마 검증 실패: {e}")
            raise HTTPException(
                status_code=500,
                detail="분석 엔진 응답 형식이 예상과 다릅니다.",
            )

        except Exception as e:
            logger.error(f"[Analyzer] 알 수 없는 에러: {repr(e)}")
            raise HTTPException(status_code=500, detail=f"분석 엔진 처리 중 에러: {e}")


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/analyze-message", response_model=AnalyzeResponse)
async def analyze_message(req: AnalyzeRequest):
    """
    1) text에서 URL 추출
    2) URL 목록으로 DB에서 블랙리스트 매칭   
        - 하나라도 매칭되면 100점 응답
        - 매칭 안되면 분석엔진에 분석 요청
    3) 분석 엔진 응답을 그대로 반환
    """

    # 1. URL 추출
    urls = extract_urls(req.text)

    # 2. 여러 URL 중 하나라도 블랙리스트와 매칭되는지 확인
    for url in urls:
        if await exists_in_blacklist(url):
            # 매칭되면 즉시 100점 반환
            return AnalyzeResponse(
                total_score=100,
                risk_level="심각",
                context_score=70,
                url_score=30,
                smishing_type="BLACKLIST_MATCH",
                reason=f"문자 내 URL 중 블랙리스트에 등록된 URL 발견: {url}",
                official_url=None,
                sender_status=None,
            )
    
    # 3. DB에서 매칭된 URL이 없다면 분석엔진 호출
    analysis = await call_analyzer(
        text=req.text,
        sender_number=req.sender_number,
    )

    return analysis