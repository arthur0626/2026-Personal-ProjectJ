# PRD — Personal DevOS v5

## 문서 상태

이 문서는 2026-10-14, 2026-10-20 결정 사항을 반영한 최신 작업 계획이다.
`prd_v5.md`를 현재 작업 계획의 기준으로 사용한다. 제품 요구사항, 보안
원칙, human checkpoint, 마일스톤 정의는 `prd_v3.md`(및 `prd_v2.md`)를
계승하고, 인증·계정 정책은 `prd_v4.md`를 계승한다. 이 문서와 이전 문서가
다르면 이 문서가 우선한다. `prd_v3.md`, `prd_v4.md`는 이력으로 보존한다.

## 2026-10-14 결정 사항

1. **Milestone 4.5a — 블로그 에디터·첨부·댓글**을 Milestone 5 앞에 추가한다.
2. **블로그 UI 디자인 정리**는 Milestone 10(Dashboard and hardening)으로
   미룬다. 4.5a는 기능만 구현하고 화면은 기존처럼 최소 마크업을 유지한다.
3. **Milestone 3 잔여 작업**(재연결, 마지막 로그인 수단 해제 방지, 탈퇴)은
   2026-10-13 결정대로 가장 마지막에 진행한다. 배포(Milestone 11) 전후
   순서는 그 시점에 owner가 정한다.
4. Phase 1 범위에 리치 텍스트 본문, 이미지·파일 첨부, 댓글(회원·비회원)을
   추가한다. 그 외 금지 범위(`AGENTS.md`의 v2 scope)는 그대로 유지한다.

## 2026-10-20 결정 사항

1. **배포(Milestone 11)를 Milestone 7 앞으로 당긴다.** webhook 수신과 Kakao
   redirect가 실제 고정 HTTPS 주소를 쓰게 하기 위해서다. Milestone 10의
   "Dockerfile·Compose 검증"도 이때 함께 한다. 대시보드·UI 정리는 그대로
   Milestone 10에 남는다.
2. **Checkpoint D**: 배포 대상은 AWS EC2 1대(`docker compose`), 도메인은
   owner가 구매한다(Route 53 권장). Kubernetes·자동 배포(CD)는 하지 않는다.
   테스트 자동화(CI, GitHub Actions)는 허용한다. Terraform은 11/09 이후 검토한다.
3. **Checkpoint B**: 풀이 저장소는 `arthur0626/2026-Coding-Test`다.
   BaekjoonHub가 안정적이지 않으므로 Milestone 7을 다음 두 단계로 바꾼다.
   - **7a — 사이트 → GitHub 커밋 (필수)**: owner가 사이트에 풀이를
     붙여넣으면 서버가 GitHub Contents API로 저장소에 커밋하고 커밋 SHA와
     파일 경로를 `CodingSubmission`에 저장한다. 경로는 BaekjoonHub 형식
     (`SWEA/D1/2063. 중간값 찾기/중간값 찾기.cpp`)을 따른다. 소스 코드만
     올리고 문제 본문(README)은 올리지 않는다. 다른 사이트(SWEA,
     프로그래머스)의 코드를 자동으로 읽는 기능은 만들지 않는다(브라우저
     수집기 금지).
   - **7b — GitHub → 사이트 webhook (시간이 되면 11/09 전, 아니면 12/05
     전)**: 서명된 push webhook을 받아, 사이트를 거치지 않은 커밋은 새
     기록으로 만들고 7a가 만든 커밋(같은 저장소·SHA·경로)은 멱등하게
     무시한다. 기존 `prd_v3.md` Milestone 7 요구사항(서명 검증, 멱등성,
     저장소·브랜치 필터)은 7b에 적용한다.
   - 필요한 secret: 이 저장소에만 Contents 쓰기 권한이 있는 GitHub
     fine-grained token (`GITHUB_ACCESS_TOKEN`). 7a 시작 시 owner가 발급한다.
4. Phase 1 완료 기준 1번("signed GitHub webhook으로 유입")은 "사이트 입력 후
   GitHub 커밋(7a) 또는 signed webhook(7b)으로 유입"으로 바꾼다.

## 현재 마일스톤 순서

| 순서 | 마일스톤 | 상태 |
|---|---|---|
| 1 | Foundation | 완료 |
| 2 | Native authentication | 완료 |
| 3 | Kakao OAuth/linking 기본 흐름 | 완료 (잔여 보안 작업은 마지막) |
| 4 | Native blog | 완료 |
| 4.5a | 블로그 에디터·첨부·댓글 | 완료 |
| 5 | Activity and coding domain | 완료 |
| 6 | Celery foundation | 완료 |
| 11 | Deployment (Docker·EC2·도메인·HTTPS) | 진행 중 |
| 7a | 사이트 → GitHub 커밋 | 대기 |
| 7b | GitHub → 사이트 webhook | 시간이 되면 |
| 8 | LLM analysis | 대기 |
| 9 | Automated blog draft | 대기 |
| 10 | Dashboard and hardening + 블로그 UI 정리 | 대기 |
| 3 잔여 | 계정 보안(재연결·탈퇴·마지막 수단 잠금) | 마지막 |

각 마일스톤의 작업 절차와 owner 확인 규칙은 `prd_v3.md`의
"Revised working procedure"를 따른다.

## Milestone 4.5a — 블로그 에디터·첨부·댓글

### 목표

네이버 블로그·디시인사이드 수준의 기본 글쓰기와 댓글 기능을 Django
템플릿 위에서 제공한다. React 전환이나 별도 프론트엔드 빌드는 하지 않는다.

### 본문 에디터

- WYSIWYG 에디터 스크립트를 CDN으로 불러온다(빌드 도구 없음).
- 제목, 굵게/기울임/밑줄/취소선, 목록, 인용, 코드 블록, 링크,
  **가운데·오른쪽 정렬**, 이미지·파일 삽입을 지원한다.
- 본문은 HTML로 저장한다. Milestone 9의 자동 초안도 같은 형식을 쓴다.
- **저장 시 서버에서 허용 목록 기반 HTML sanitize**를 한다. 저장 경로가
  폼·admin·자동 초안 어디든 동일하게 적용되도록 모델 저장 단계에서
  처리한다. 스크립트, 이벤트 속성, `style` 속성, `data:`/`javascript:`
  URL은 제거한다.
- 기존 평문 본문(``` 코드 블록 포함)은 마이그레이션으로 HTML로 변환한다.
- 스티커 전용 기능은 만들지 않는다. 이모지 입력으로 대신한다.

### 첨부 (이미지·파일)

- owner(staff)만 업로드할 수 있다. CSRF 보호를 유지한다.
- 이미지: Pillow로 실제 이미지인지 검증하고 다시 인코딩해 **EXIF(GPS
  위치 등)를 제거**한다. 허용 형식은 JPEG, PNG, GIF, WebP이다.
- 파일: 확장자 허용 목록만 받는다. HTML, SVG, 실행 파일 등 브라우저에서
  스크립트로 실행될 수 있는 형식은 받지 않는다.
- 크기 제한: 파일당 10MB.
- 개발 환경에서는 로컬 `media/`에 저장하고 `DEBUG`일 때만 Django가
  서빙한다. 운영 저장소(서버 디스크 또는 외부 스토리지)와 다운로드
  헤더 정책은 Milestone 11에서 결정한다.

### 댓글

- 공개(발행 + 공개 범위) 글에만 댓글을 쓸 수 있다.
- **회원**: 로그인 계정으로 작성하고 닉네임은 계정 이름을 사용한다.
- **비회원**: 디시인사이드처럼 닉네임과 비밀번호를 그 자리에서 입력해
  작성한다. 비밀번호는 Django 해시로 저장하며 평문을 남기지 않는다.
- 비회원 댓글은 화면에 "(비회원)"으로 구분해 회원·owner 사칭을 막는다.
- 삭제: 회원은 본인 댓글, 비회원은 작성 시 비밀번호로, owner(staff)는
  모든 댓글을 삭제할 수 있다. 수정 기능은 두지 않는다.
- 댓글 본문은 평문으로 저장하고 출력 시 escape한다(HTML 불허).
- 스팸 방지 최소 조치: 길이 제한, honeypot 필드. IP 기반 rate limit과
  신고 기능은 Milestone 10 hardening에서 검토한다.

### 하지 않는 것

- 블로그 UI 디자인 정리(Milestone 10)
- 댓글 수정, 대댓글, 알림, 좋아요
- 첨부 파일의 운영 스토리지 구성(Milestone 11)

### 완료 기준

```bash
venv/bin/python manage.py check
venv/bin/python manage.py makemigrations --check
venv/bin/python manage.py migrate
venv/bin/python manage.py test
```

- sanitize가 스크립트·이벤트 속성·위험 URL을 제거하는 테스트
- 기존 평문 본문 변환 테스트
- 비 staff 업로드 거부, 허용되지 않은 형식 거부, EXIF 제거 테스트
- 비공개·초안 글 댓글 거부, 비회원 비밀번호 해시 저장, 삭제 권한 테스트

완료 후 owner 확인을 받고 Milestone 5로 이동한다.

## Milestone 10 추가 범위 — 블로그 UI 정리

`prd_v3.md`의 Milestone 10 범위에 다음을 추가한다.

- 공통 레이아웃(base 템플릿), 블로그 목록·상세·에디터·댓글 화면 정리
- 모바일 반응형
- 댓글 rate limit·신고 등 hardening 검토
