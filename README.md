# Personal DevOS

`prd_v3.md`를 기준으로 개발하는 Django 기반 Personal DevOS입니다.

현재 구현 범위는 **Milestone 4 — Native blog**까지입니다. Milestone 3의
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

현재 `activity`, `coding`, `integrations`, `common`은 다음
마일스톤에서 도메인 모델과 기능을 채울 수 있도록 최소 골격만 존재합니다.

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
- 본문은 전부 escape되고 ``` 코드 블록만 `<pre><code>`로 렌더링됩니다. 전체
  Markdown은 지원하지 않습니다.
- `BlogPost.author`는 `PROTECT`입니다. 탈퇴 시 글 처리 정책이 확정되기 전까지
  글이 있는 User는 삭제되지 않습니다.
- `source_submission`/`source_analysis` 연결과 태그는 해당 모델이 생기는
  Milestone 5·9에서 추가합니다.

## 중요한 규칙

- `prd_v3.md`가 구현 기준입니다.
- `prd.md`는 기존 문서로 보존합니다.
- WordPress는 v2 Phase 1에서 구현하지 않습니다.
- Kakao, 실제 GitHub 저장소, LLM, 배포 값은 해당 체크포인트에서 확인 후 사용합니다.
- `.env`와 비밀값은 커밋하지 않습니다.
