# my-stock-team

한국 주식 협업 리서치를 위한 Claude Code 플러그인입니다. 종목명을 넣으면 애널리스트
서브에이전트들이 협업해 리서치를 만들고, 디자인된 PPTX/PDF 리포트로 내보냅니다.

## 구성

```
my-stock-team/
├── .claude-plugin/
│   ├── plugin.json          # 플러그인 매니페스트 (name: my-stock-team, 1.0.0)
│   └── marketplace.json     # 설치 카탈로그
├── agents/                  # 서브에이전트 5종
│   ├── fundamental-analyst.md        # DART 재무·공시
│   ├── market-technical-analyst.md   # 주가·추세 (FinanceDataReader)
│   ├── news-sentiment-analyst.md     # 뉴스·시장 심리 (웹 검색)
│   ├── risk-manager.md               # 리스크 종합 (pykrx)
│   └── report-validation-analyst.md  # 리포트 품질 검증
├── commands/
│   └── stock-research.md    # /stock-research — 전체 파이프라인 실행
└── skills/
    └── report-pptx/         # 리서치 md → 디자인 PPTX/PDF
        ├── SKILL.md
        └── scripts/{build_pptx.py, build_pdf.py}
```

## 설치

```
# 마켓플레이스 등록 후 설치
/plugin marketplace add <이 저장소 경로 또는 URL>
/plugin install my-stock-team@my-stock-team-marketplace
```

## 사용

```
/stock-research 삼성전자
/stock-research 삼성전자 SK하이닉스
```

개별 에이전트도 직접 호출할 수 있습니다(예: "삼성전자 추세 봐줘" → market-technical-analyst).

## 사전 요구사항

**비밀값은 이 플러그인에 포함되어 있지 않습니다.** 각자 환경에서 설정하세요.

- **DART_KEY** (재무 분석용): [DART 오픈API](https://opendart.fss.or.kr)에서 무료 발급 후
  사용 프로젝트의 `.env` 또는 환경변수로 설정합니다. (없어도 재무 외 분석은 동작하며, 재무는 "확인 불가" 처리)
- **Python 패키지**:
  ```
  pip install python-pptx fpdf2 finance-datareader pykrx opendartreader pandas
  ```
- **한글 폰트**: 리포트는 맑은 고딕(`malgun.ttf`)을 사용합니다(Windows 기본 탑재).

## 가드레일

모든 산출물은 다음을 지킵니다 — 수치마다 출처·기준일, 못 구한 값은 "확인 불가"/소문은 "미확인",
투자 행동(매수·매도·목표가 등) 단정 금지(의사결정 지원까지만), 리포트 머리·꼬리에 학습용 고지.
리포트 렌더러는 투자 행동 단정 표현을 자동 검출해 빌드를 막습니다.

> 본 플러그인의 산출물은 무료 공개 데이터 기반 학습용이며 투자 권유가 아닙니다.
