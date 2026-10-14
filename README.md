# Personal DevOS

`prd_v5.md`를 기준으로 개발하는 Django 기반 Personal DevOS입니다.

현재 구현 범위는 **Milestone 5 — Activity and coding domain**까지입니다. Milestone 3의
남은 계정 보안 작업(재연결, 탈퇴)은 owner 결정으로 마지막에 진행합니다.

## 기술 기반

- Python virtual environment: `venv/`
- Django
- PostgreSQL
- Redis + Celery 기반을 위한 설정
- Django templates
- 모듈형 monolith 구조

## 로컬 실행

Docker가 설치되어 있다면 PostgreSQL과 Redis를 먼저 실행합니다.

```bash
docker compose up -d postgres redis
```

그 다음 의존성을 설치하고 Django 점검을 실행합니다.

```bash
venv/bin/pip install -r requirements.txt
venv/bin/python manage.py check
venv/bin/python manage.py migrate
venv/bin/python manage.py runserver
```

현재 PostgreSQL 서버가 실행 중이지 않으면 `check`는 통과할 수 있지만,
`migrate`와 테스트는 DB 연결 오류로 실패합니다.

## 테스트

```bash
venv/bin/python manage.py test
```

테스트는 PostgreSQL 테스트 데이터베이스를 사용합니다.

## 현재 앱 경계

```text
accounts/       사용자와 인증
activity/       ActivityEvent
coding/         코딩 제출과 parser
blog/           native Django BlogPost
integrations/   GitHub 및 외부 서비스 adapter
common/         작은 공용 유틸리티
config/         Django 설정, URL, Celery
```

의존 방향은 `coding → activity`, `blog/coding/activity → common`입니다.
`activity`는 다른 도메인 앱을 import하지 않고, 타임라인 템플릿만 역참조
(`event.coding_submission`)로 상세 링크를 만듭니다. `integrations`는
Milestone 7부터 채웁니다.

## Milestone 3 설계 메모

- Kakao provider URL은 연결했지만 실 OAuth 호출은 Checkpoint A 이후에만 사용합니다.
- 로그인한 사용자가 명시적으로 연결을 시작할 때만 `process=connect` 흐름을 사용합니다.
- social-only 사용자는 계정 설정에서 네이티브 비밀번호를 추가할 수 있습니다.
- 유일한 로그인 수단인 소셜 계정은 네이티브 비밀번호를 추가하기 전까지 해제할 수 없습니다.
- Kakao 프로필 원문은 사용자 모델이나 `SocialAccount.extra_data`에 보존하지 않습니다.

## Milestone 4 설계 메모

- 공개 경로(`/blog/`, `/blog/<slug>/`)는 `BlogPost.objects.public()`만 조회합니다.
  이 queryset은 `status=published`와 `visibility=public`을 함께 요구합니다.
- 글 작성·수정·발행(`/blog/drafts/…`)은 `is_staff` 계정만 가능합니다. 회원가입이
  열려 있으므로 일반 가입자는 403을 받습니다. owner 계정은 `createsuperuser`로
  만들거나 admin에서 staff 권한을 부여합니다.
- 관리 화면의 모든 조회는 `author=request.user`로 제한되어, 다른 staff의 글을
  ID 추측으로 수정하거나 발행할 수 없습니다.
- 작성자는 자신의 초안과 비공개 글을 `/blog/<slug>/`에서 미리 볼 수 있습니다.
- 발행은 POST로만 가능하며 `published_at`은 발행 시 설정되고 초안으로 되돌리면
  비워집니다.
- `BlogPost.author`는 `PROTECT`입니다. 탈퇴 시 글 처리 정책이 확정되기 전까지
  글이 있는 User는 삭제되지 않습니다.
- `source_submission`/`source_analysis` 연결은 자동 초안을 만드는 Milestone 9에서
  추가합니다.

## Milestone 4.5a 설계 메모

- 에디터는 Quill 2(CDN)이며 본문은 HTML로 저장합니다. `BlogPost.save()`가 매번
  `nh3` 허용 목록으로 sanitize하므로 폼·admin·자동 초안 모두 같은 검사를 거칩니다.
  상세 화면의 `|safe`는 이 검사를 전제로 합니다.
- 기존 평문 본문은 `blog/migrations/0003`에서 HTML로 변환했습니다(되돌릴 수 없음).
- 첨부 업로드(`/blog/uploads/`)는 staff만 가능하고 10MB, 확장자 허용 목록을
  적용합니다. 이미지는 회전을 적용한 뒤 다시 인코딩해 EXIF(GPS)를 제거합니다.
- 업로드 파일은 `media/`에 저장되며 `DEBUG`일 때만 Django가 서빙합니다.
- 댓글은 공개 글에만 가능합니다. 비회원은 닉네임과 비밀번호(해시 저장)로 쓰고
  "(비회원)"으로 표시되며, 비밀번호·본인·staff만 삭제할 수 있습니다.
- 비회원 비밀번호 시도 제한과 미사용 첨부 정리는 각각 Milestone 10·11에서 합니다.

## Milestone 5 설계 메모

- `ActivityEvent`는 "활동이 일어났다"는 공통 사실만 담고, 코딩 세부 정보는
  `CodingSubmission`(1:1)에 둡니다.
- `CodingSubmission.record()`가 이벤트와 제출을 한 트랜잭션으로 만듭니다. 직접
  입력(`/coding/new/`)과 Milestone 7의 GitHub 수집이 같은 경로를 씁니다.
- 소스 코드는 입력 그대로 저장합니다(폼의 공백 제거도 끔).
- 같은 `repository + commit_sha + file_path`는 한 번만 저장됩니다(중복 수집 방지).
  커밋이 없는 직접 입력은 이 제약을 받지 않습니다.
- `CodeAnalysis`는 제출당 여러 개를 허용합니다(재시도·프롬프트 버전). 화면에는
  항상 "AI가 생성한 분석, 검토 필요" 문구가 붙습니다.
- `/coding/`, `/activity/`는 staff 전용이며 자기 데이터만 보입니다. 이벤트·제출의
  `user`는 탈퇴 정책 확정 전까지 `PROTECT`입니다.

## 중요한 규칙

- `prd_v5.md`가 구현 기준입니다(`prd_v2`~`v4`는 이력).
- `prd.md`는 기존 문서로 보존합니다.
- WordPress는 v2 Phase 1에서 구현하지 않습니다.
- Kakao, 실제 GitHub 저장소, LLM, 배포 값은 해당 체크포인트에서 확인 후 사용합니다.
- `.env`와 비밀값은 커밋하지 않습니다.
