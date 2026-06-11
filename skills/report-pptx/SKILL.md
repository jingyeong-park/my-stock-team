---
name: report-pptx
description: reports/{종목명}.md 리서치 문서를 읽어 디자인된 PPTX 리포트(reports/{종목명}.pptx)를 생성한다. 사용자가 "PPTX 만들어줘", "리포트 내보내줘", "/report-pptx 종목명" 등 리서치 결과를 슬라이드로 변환해 달라고 할 때 사용한다.
argument-hint: "{종목명} — reports/{종목명}.md 가 있어야 함"
---

# report-pptx: 리서치 md → 디자인 PPTX

## 입출력 계약

- 입력: `reports/{종목명}.md` (협업 리서치 결과 문서)
- 출력: `reports/{종목명}.pptx`
- 렌더링: `${CLAUDE_PLUGIN_ROOT}/skills/report-pptx/scripts/build_pptx.py` (디자인·폰트·표 잘림 처리는 전부 스크립트에 고정되어 있음 — 직접 python-pptx 코드를 새로 짜지 말 것)

## 수행 절차

1. **입력 확인**: `reports/{종목명}.md`를 읽는다. 파일이 없으면 `reports/`의 .md 목록을 보여주고 사용자에게 확인한다. 종목명이 인자로 안 왔으면 물어본다.
2. **spec JSON 작성**: md 내용을 아래 스키마로 추출해 `reports/_build/{종목명}.spec.json`에 저장한다 (UTF-8).
3. **렌더링 실행**:
   ```
   python ${CLAUDE_PLUGIN_ROOT}/skills/report-pptx/scripts/build_pptx.py "reports/_build/{종목명}.spec.json" "reports/{종목명}.pptx"
   ```
   사용자가 PDF를 원하거나 PPTX를 볼 수 없는 환경이면 같은 spec으로 PDF도 생성한다 (동일 디자인, fpdf2 사용):
   ```
   python ${CLAUDE_PLUGIN_ROOT}/skills/report-pptx/scripts/build_pdf.py "reports/_build/{종목명}.spec.json" "reports/{종목명}.pdf"
   ```
4. **exit code 2(금지 표현 검출)** 가 나오면 출력에 표시된 문구를 가드레일에 맞게 고쳐 쓰고(아래 콘텐츠 규칙 참조) 재실행한다.
5. 생성된 .pptx 경로와 슬라이드 구성을 사용자에게 보고한다.

## spec JSON 스키마

슬라이드 순서는 스크립트가 고정한다: 표지 → 종목 개요 → 재무 요약 → 가격/추세 → 뉴스·심리 → 리스크 → 한 줄 종합.

```json
{
  "ticker_name": "삼성전자",
  "ticker_code": "005930",
  "date": "2026-06-11",
  "overview": { "bullets": ["문장 (출처: ..., 기준일 ...)", "... 최대 7개"] },
  "financials": {
    "columns": ["항목", "2023", "2024", "2025"],
    "rows": [["매출액", "...", "...", "..."], ["영업이익", "...", "...", "..."]],
    "bullets": ["해석 코멘트 최대 4개"],
    "note": "출처: DART 사업보고서, 기준일 YYYY-MM-DD"
  },
  "price": {
    "chart": {
      "categories": ["2026-01-02", "..."],
      "series": [{ "name": "종가", "values": [55000, ...] }]
    },
    "bullets": ["추세 요약 최대 7개 (각 항목에 출처·기준일)"],
    "source": "출처: FinanceDataReader, 기준일 YYYY-MM-DD"
  },
  "news": {
    "bullets": [{ "text": "이슈 한 줄", "source": "(출처: 매체, YYYY-MM-DD)" }],
    "sentiment": "중립 — 한 줄 근거"
  },
  "risks": [
    { "title": "리스크명", "basis": "근거 (어느 분석/데이터)", "impact": "발생 시 영향" }
  ],
  "summary": {
    "line": "한 줄 종합 (판단 근거까지만, 단정 금지)",
    "bullets": ["보조 포인트 최대 3개 (선택)"]
  }
}
```

- `price.chart`는 md에 시계열 수치가 있을 때만 넣는다. 없으면 생략(bullets만으로 렌더링됨). md에 차트용 시계열이 없고 종목코드를 알면, FinanceDataReader로 최근 6개월 종가를 조회해 채워도 된다(실패 시 생략).
- 재무 표는 **최근 3개년** 컬럼을 기본으로 한다. 본문 행은 8행 이하 권장(초과분은 스크립트가 자동 절단하고 "N행 생략" 표기).

## 콘텐츠 규칙 (CLAUDE.md 가드레일 적용)

- **출처 없는 수치는 싣지 않는다.** md에서 수치를 가져올 때 출처·기준일이 함께 없으면 그 수치는 버리거나, md 안에서 출처를 찾아 붙인다. 못 찾으면 제외.
- **매수/매도 단정·목표가 금지.** "매수 추천", "사야 합니다", "목표주가 X원" 등은 쓰지 않는다. 외부 증권사 목표가 보도를 인용해야 하면 가격 수치 없이 "증권사 투자의견 상향 보도(출처: ...)" 식으로 바꾼다. 스크립트가 금지 표현을 검출하면 exit 2로 실패한다.
- 모든 문장은 "~입니다" 체. summary.line은 결론 우선, 근거는 핵심만.
- 학습용 면책 문구는 스크립트가 모든 슬라이드 푸터에 자동 삽입하므로 spec에 따로 넣지 않는다.

## 디자인 (스크립트 고정 — 변경하려면 build_pptx.py 수정)

- 16:9, KB 옐로우 #FFBC00 포인트 + 다크그레이 본문/화이트 배경
- 전체 폰트 맑은 고딕 (latin+EA 동시 지정으로 한글 깨짐 방지)
- 표: 헤더 옐로우, 본문 줄무늬, 행 초과 시 자동 절단
- 차트: 라인 차트, 포인트 30개 초과 시 자동 다운샘플
