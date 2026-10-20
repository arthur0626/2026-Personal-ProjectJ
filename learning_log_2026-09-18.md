# Personal DevOS 학습·개발 기록

## 날짜

- 2026-09-18
- 기록 시간: 15:31 KST
- 작업 시간대: 오후 개발 세션

## 오늘 한 것

1. `prd_v2.md`와 현재 Django 프로젝트 구조를 분석했다.
2. 현재 프로젝트가 Foundation과 Native Authentication을 일부 구현한 상태임을 확인했다.
3. `manage.py check`는 통과하지만 PostgreSQL 연결 문제로 테스트와 migration이 막혀 있음을 확인했다.
4. PostgreSQL은 주 데이터베이스이고 Redis는 Celery 비동기 작업용 broker라는 점을 정리했다.
5. Docker를 초기 개발의 필수 도구로 사용하지 않고, 로컬 개발을 먼저 진행한 뒤 배포 단계에서 Docker를 도입하기로 결정했다.
6. 이 방향을 반영해 `prd_v3.md`를 만들고 `AGENTS.md`의 source of truth를 변경했다.
7. PostgreSQL 서버를 실행하고 `accepting connections` 상태를 확인했다.
8. PostgreSQL role 이름과 Linux 사용자 이름은 별개라는 점을 확인했다.
9. PostgreSQL role 이름의 오타(`person_dev_os_app` / `personal_dev_os_app`)를 수정했다.
10. `venv/bin/python manage.py test`를 실행해 6개 테스트가 모두 통과했다.

## 배운 내용

- Django가 PostgreSQL에 연결할 때는 `DATABASE_URL`의 사용자명, 비밀번호, 호스트, 포트, 데이터베이스명이 모두 실제 PostgreSQL 설정과 일치해야 한다.
- `password authentication failed`는 서버에는 도달했지만 사용자명 또는 비밀번호가 맞지 않는다는 의미다.
- 데이터베이스가 없을 때는 보통 `database does not exist` 오류가 발생한다.
- PostgreSQL의 기본 관리자 role은 일반적으로 `postgres`지만, 애플리케이션 전용 role을 별도로 만드는 것이 더 현업적인 구성이다.
- Linux 계정명과 PostgreSQL role명을 같게 만들 필요는 없다.
- Docker는 애플리케이션 개발의 필수 조건이 아니라 배포 환경을 재현하기 위한 도구로도 사용할 수 있다.
- PostgreSQL은 Milestone 1부터 필요하지만, Redis는 Celery를 도입하는 Milestone 6부터 필요하다.
- Render 무료 서비스는 학습·실험에는 사용할 수 있지만 무료 데이터베이스의 보존성, 수면, 만료, 백업 제한을 확인해야 한다.

## 기억할 것

- PostgreSQL 애플리케이션 role 이름은 `personal_dev_os_app`으로 사용한다.
- 이 role은 Linux 사용자 `arthur0626`과 다른 별도의 데이터베이스 계정이다.
- 로컬 개발용 role은 테스트 데이터베이스 생성을 위해 `CREATEDB` 권한이 필요할 수 있다.
- 운영 환경에서는 애플리케이션 role에 불필요한 관리자 권한을 주지 않는다.
- 프로젝트의 현재 구현 기준은 `prd_v3.md`다.
- Docker는 Milestone 10에서 Dockerfile과 Compose를 검증하고, Milestone 11에서 배포에 사용한다.
- `.env`, 비밀번호, API key, OAuth secret, webhook secret은 커밋하지 않는다.
- Kakao, 실제 GitHub 저장소/webhook, LLM provider/API key, 배포 secret은 각 human checkpoint 전까지 사용하지 않는다.
- PostgreSQL과 Redis가 실행 중이어도 Django의 연결 설정이 다르면 migration과 테스트는 실패한다.
- 테스트 결과가 `Ran 6 tests ... OK`이면 현재 작성된 Foundation/인증 테스트가 통과한 것이다.

## 추가 학습 — PostgreSQL 테스트와 DATABASE_URL

### PostgreSQL을 사용하는데 왜 테스트하는가

PostgreSQL은 데이터를 저장하는 실제 장소이고, 테스트는 애플리케이션이
그 장소와 약속한 방식으로 제대로 대화하는지 확인하는 과정이다. 테스트를
하지 않으면 회원가입, 로그인, migration 등이 실제 데이터베이스에서
작동하는지 알 수 없다.

### 왜 테스트가 6개인가

현재 프로젝트의 테스트 파일에 독립적인 테스트 함수가 6개 작성되어 있기
때문이다. 6단계의 PostgreSQL 절차라는 뜻이 아니다. 각 테스트는 홈 접근,
회원가입, 로그인, 비로그인 접근 제한, 로그아웃, 계정 설정 보호처럼 서로
다른 동작 하나를 확인한다.

### 왜 `default` 데이터베이스를 만들고 테스트 후 파괴하는가

`default`는 특별한 PostgreSQL 데이터베이스 이름이 아니라 Django가
기본으로 사용할 데이터베이스 연결에 붙인 별명(alias)이다.

테스트를 시작하면 Django는 `default` 설정을 참고해 실제 프로젝트
데이터베이스와 분리된 테스트용 데이터베이스를 만든다. 테스트가 끝나면
그 테스트 데이터베이스를 삭제한다. 이렇게 해야 테스트가 실제 사용자
데이터를 지우거나 다음 테스트에 남은 데이터를 전달하지 않는다.

비유하면 실제 데이터베이스는 원본 작업실이고, 테스트 데이터베이스는
실험이 끝나면 버리는 연습용 작업실이다.

### `DATABASE_URL`의 구조

```text
postgres://아이디:비밀번호@호스트:포트/데이터베이스이름
```

- `postgres://`: PostgreSQL에 접속한다는 방식(scheme)
- `아이디`: PostgreSQL role 이름
- `비밀번호`: 그 role의 인증 비밀번호
- `호스트`: 데이터베이스 서버 주소
- `포트`: PostgreSQL이 연결을 기다리는 문 번호이며 기본값은 5432
- `데이터베이스이름`: 사용할 데이터 저장 공간

이 방식은 PostgreSQL만의 특별한 문법이 아니라 URI/DSN이라는 널리 쓰이는
연결 문자열 형식이다. 다른 웹사이트와 서버 애플리케이션도 데이터베이스,
Redis, 메시지 큐 등에 비슷한 형식을 자주 사용한다. 다만 어떤 서비스는
`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`처럼 항목을 각각의 환경변수로
나누어 사용하기도 한다.

`DATABASE_URL`은 코드를 바꾸지 않고 개발·테스트·배포 환경마다 다른
데이터베이스를 연결하기 위해 환경변수로 관리한다. 비밀번호에 `@`, `:`
같은 문자가 있으면 URL 인코딩이 필요하며, 이 값은 절대 Git에 커밋하지
않는다.

이번 학습으로 PostgreSQL 테스트의 목적, Django 테스트 데이터베이스의
격리와 삭제, `default` alias의 의미, `DATABASE_URL`의 URI 구조를 공부했다.

## 세션 종료 기록 — 2026-09-19

### 오늘 진행한 내용 전체 요약

- `prd_v2.md`와 현재 `my_app`의 Django 구조를 비교하여 마일스톤 진행 상태를 분석했다.
- 현재 프로젝트는 Foundation과 Native Authentication이 대부분 구현되어 있고, Kakao OAuth부터는 아직 준비 단계임을 확인했다.
- `manage.py check`는 통과했지만 PostgreSQL 연결이 되지 않아 migration과 테스트가 처음에는 실패했다.
- Docker를 초기 개발의 필수 도구로 사용하지 않고, PostgreSQL은 로컬에서 먼저 사용하며 Docker는 배포 전 단계에 도입하기로 결정했다.
- 이 개발 방향을 반영하여 `prd_v3.md`를 작성했다.
- `AGENTS.md`의 구현 기준을 `prd_v3.md`로 변경했다.
- PostgreSQL 서버를 실행하고 `accepting connections` 상태를 확인했다.
- Linux 사용자명과 PostgreSQL role 이름이 서로 별개라는 점을 확인했다.
- 애플리케이션 전용 PostgreSQL role 이름을 `personal_dev_os_app`으로 결정했다.
- 처음에는 role 이름 오타인 `person_dev_os_app`을 사용하여 인증 오류가 발생했다.
- `.env`의 role 이름을 수정한 뒤 PostgreSQL 연결과 Django 테스트를 정상화했다.
- Django 테스트 6개가 다음 결과로 통과했다.

```text
Ran 6 tests in 0.817s
OK
```

- 실제 웹 화면에서 `arthur0626` 계정 가입까지 완료하여 회원가입 기능을 확인했다.
- PostgreSQL 테스트 데이터베이스의 생성·삭제 이유와 Django `default` database alias의 의미를 공부했다.
- `DATABASE_URL`의 URI 구조와 다른 서비스에서도 유사한 연결 문자열을 사용한다는 점을 공부했다.

### 오늘 확인한 최종 상태

- Django system check: 통과
- PostgreSQL 서버: 연결 가능 상태 확인
- PostgreSQL 인증: role 이름 수정 후 정상화
- Django 테스트: 6개 모두 통과
- 회원가입 화면: 정상 작동 확인
- 현재 프로젝트 진행 단계: Milestone 1 검증 완료에 가까운 상태
- 다음 개발 순서: Native Authentication 정리 후 Kakao OAuth 준비

### 종료 전 기억할 내용

- `personal_dev_os_app`은 PostgreSQL role이며 Linux 사용자 `arthur0626`과 다르다.
- `DATABASE_URL`의 사용자명과 PostgreSQL role 이름은 철자까지 정확히 일치해야 한다.
- `default`는 데이터베이스 이름이 아니라 Django의 기본 연결 alias다.
- Django 테스트는 실제 데이터를 보호하기 위해 별도의 테스트 데이터베이스를 만들고 테스트 후 삭제한다.
- Docker는 매일 쓰는 개발 도구가 아니라 Milestone 10~11에서 배포를 재현하는 도구로 도입한다.
- `.env`와 비밀번호, API key, OAuth secret은 기록 파일이나 Git에 남기지 않는다.
- 다음 작업을 시작할 때 `prd_v3.md`를 기준으로 한 마일스톤만 진행하고, 완료 후 owner 확인을 받는다.

## 다음 실행 명령

PostgreSQL 관리자 계정으로 접속한다.

```bash
sudo -u postgres psql
```

애플리케이션 전용 role과 데이터베이스를 만든다.

```sql
CREATE ROLE personal_dev_os_app WITH LOGIN PASSWORD '원하는_비밀번호';
ALTER ROLE personal_dev_os_app CREATEDB;
CREATE DATABASE personal_dev_os OWNER personal_dev_os_app;
\q
```

이미 role이나 데이터베이스가 존재한다는 메시지가 나오면 해당 생성 명령은
건너뛰고, 필요한 경우 다음처럼 비밀번호만 변경한다.

```sql
ALTER ROLE personal_dev_os_app WITH LOGIN PASSWORD '원하는_비밀번호';
```

`.env`의 데이터베이스 설정은 다음 형식으로 맞춘다.

```env
DATABASE_URL=postgres://personal_dev_os_app:원하는_비밀번호@127.0.0.1:5432/personal_dev_os
```

마지막으로 Django를 검증한다.

```bash
venv/bin/python manage.py check
venv/bin/python manage.py migrate
venv/bin/python manage.py test
```

## 학습 기록 — 2026-09-19

### 오늘 공부한 내용

- PostgreSQL의 서버, 클러스터, 데이터베이스, role, 테이블의 관계를 공부했다.
- `pg_lsclusters` 결과에서 PostgreSQL 18의 `main` 클러스터가 이미 생성되어 있고 `online` 상태임을 확인했다.
- PostgreSQL 패키지 설치 과정에서 기본 클러스터가 자동으로 만들어질 수 있다는 점을 배웠다.
- `pg_ctlcluster 16 main start`가 실패한 이유는 PostgreSQL 16 클러스터가 없고, 실제 설치·실행 중인 버전은 18이기 때문이었다.
- `sudo -u postgres`의 `-u`는 Linux 사용자를 지정하는 옵션이고, PostgreSQL 접속 사용자 지정은 보통 `psql -U`를 사용한다.
- `-h`는 host, `-p`는 port를 의미하며 `--version`은 프로그램 버전을 요청하는 긴 옵션이다.
- 짧은 옵션과 긴 옵션은 명령어가 정의한 문법이며, 같은 글자라도 명령어에 따라 의미가 달라질 수 있다.
- 호스트는 PostgreSQL이 실행 중인 컴퓨터 주소이고, 포트는 해당 컴퓨터에서 서버 프로그램을 구분하는 번호라는 점을 이해했다.
- `127.0.0.1`은 현재 컴퓨터의 loopback 주소이며, `localhost`는 일반적으로 이 주소로 해석된다.
- `127.0.0.2`가 일반적인 기본값인 것은 아니며, `0.0.0.0`은 모든 네트워크 인터페이스에서 접속을 받겠다는 서버 bind 주소라는 점을 배웠다.
- Django, PostgreSQL, Minecraft처럼 프로그램마다 기본 포트가 다를 수 있지만, 프로젝트 폴더를 복사한다고 포트가 자동으로 바뀌지는 않는다.
- 같은 컴퓨터에서 같은 종류의 서버를 여러 개 실행할 때만 포트 충돌을 피하기 위해 다른 포트를 지정한다.

### 오늘 구현·검증한 Milestone 3 내용

- Kakao OAuth provider URL과 명시적 `process=connect` account linking 흐름을 추가했다.
- 로그인한 사용자가 계정 설정에서 Kakao 연결을 시작하도록 구성했다.
- social-only 계정이 네이티브 비밀번호를 추가할 수 있게 했다.
- 유일한 로그인 수단인 소셜 계정의 해제를 막도록 구성했다.
- Kakao 프로필·이메일 원문을 User와 `SocialAccount.extra_data`에 보존하지 않도록 했다.
- mock/DB 테스트와 임시 SQLite smoke test 11개가 통과했다.
- 실 Kakao credentials는 아직 사용하지 않았다.

### Milestone 3 PostgreSQL 최종 검증

사용자 환경에서 PostgreSQL 18 `main` 클러스터가 `online`이고
`127.0.0.1:5432 - accepting connections` 상태임을 확인했다.

```text
Found 11 test(s).
Ran 11 tests in 1.419s
OK
```

따라서 `manage.py check`와 PostgreSQL 기반 Milestone 3 테스트 11개가
모두 통과했다. 다음 단계는 실 Kakao OAuth 사용 전 Checkpoint A 승인이다.

### Checkpoint A 승인 후 Kakao 연동 준비

- owner가 Checkpoint A에서 실 Kakao OAuth 사용을 승인했다.
- 로그인 화면에 Kakao 로그인 진입 버튼을 추가했다.
- 설정에 Kakao client ID와 secret이 비어 있지 않음만 확인했으며, 비밀값은 출력하거나 기록하지 않았다.
- 로컬 개발 서버의 Kakao Redirect URI는 다음 경로를 사용한다.

```text
http://127.0.0.1:8000/accounts/social/kakao/login/callback/
```

- 다음 단계는 Kakao 개발자 콘솔에 위 Redirect URI를 등록한 뒤, 로컬에서 신규 social login과 기존 native 계정 linking을 수동 검증하는 것이다.

## 세션 종료 기록 — 2026-10-13

### 오늘 한 것 — 인프라/운영 세팅 (Django 기능 구현 아님)

Milestone 3 실작업 전에, Claude Code 모델 선택과 프로젝트 운영 환경을
정리하는 세션이었다.

1. `prd_v4.md`, `AGENTS.md`, `README.md`를 기준으로 프로젝트 현황을
   재확인하고, 작업 성격별 모델 추천(보안/정책 판단은 Opus, 반복 구현은
   Sonnet 5)과 OpenAI Codex 대비 Claude Code 사용 기준을 정리했다.
2. 토큰 절감 플러그인 `Ponytail`(DietrichGebert, MIT)을 조사했다. 바이너리가
   아니라 `SKILL.md`/`AGENTS.md` 기반의 markdown 규칙 묶음이며, 코드 작성
   전 "꼭 필요한가 → 기존 코드/표준 라이브러리로 되는가 → 최소 코드만"
   체크리스트를 거치게 해 출력 토큰을 줄인다는 것을 확인했다. 설치는
   아직 보류(owner 확인 후 진행).
3. `.gitignore`에 `venv/`가 빠져 있던 것을 발견해 수정했다
   (`venv/`, `media/`, `.vscode/`, `*.log`, `*.sqlite3` 등 추가).
4. `git init` 후 기본 브랜치를 `main`으로 설정하고, 전체 추적 대상 파일에
   실제 secret·API key·이메일·전화번호가 없는지 `git grep`으로 스캔해
   확인했다 (`.env.example`은 빈 값/placeholder뿐, `settings.py`는 env
   변수만 참조).
5. 스캔 결과를 근거로 private/public 저장소를 분리하지 않고, 기존 public
   저장소 `arthur0626/2026-Personal-ProjectJ` 하나에 전체를 백업하기로
   결정했다.
6. `gh` CLI는 설치에 `sudo` 비밀번호가 필요해 자동화할 수 없었다. 대신
   `ssh-keygen`으로 `ed25519` 키를 생성하고 공개키를 GitHub에 등록해
   `sudo` 없이 SSH 인증으로 push하는 방식을 사용했다.
7. 첫 커밋(`Initial backup commit`)을 만들고
   `git@github.com:arthur0626/2026-Personal-ProjectJ.git`로 push했다.
8. Notion MCP 서버(`https://mcp.notion.com/mcp`, http transport)를
   `claude mcp add`로 로컬 프로젝트 설정에 추가했다. 매일 작업물을
   Notion에 자동 업로드(cron 스케줄)하는 것이 목표이며, 우선 OAuth
   인증이 필요한 상태다.
9. owner가 Milestone 3(계정 보안/연결 해제·재연결·탈퇴)을 가장 마지막
   순서로 미루기로 결정했다.

### 배운 내용

- `claude mcp add`로 MCP 서버를 추가해도, 이미 실행 중인 세션은 시작
  시점에 MCP 목록을 불러온 상태라 즉시 반영되지 않는다. 새 서버를
  쓰려면 세션을 재시작하고 `/mcp`로 다시 확인해야 한다.
- GitHub push 인증에 꼭 `gh` CLI가 필요한 것은 아니다. `sudo` 권한이
  없어도 `ssh-keygen` + GitHub에 공개키 등록만으로 SSH push가 가능하다.
- public 저장소에 올리기 전에는 `git grep`으로 `secret`, `client_id`,
  `api_key`, 이메일/전화번호 패턴을 스캔해 실제 값인지 placeholder인지
  확인하는 것이 안전하다. placeholder/변수명과 실제 유출 값은 구분해서
  판단해야 한다.
- 서드파티 Claude Code 플러그인(Ponytail 등)은 실행형 프로그램이 아니라
  markdown 규칙(skill) 형태일 수 있으며, 이 경우 별도 시스템 권한을
  요구하지 않는다.

### 기억할 것

- GitHub 백업 저장소: `arthur0626/2026-Personal-ProjectJ` (public, 단일
  저장소로 운영, private/public 분리하지 않기로 결정).
- GitHub push는 로컬에 생성한 `~/.ssh/id_ed25519` 키로 인증한다.
- Notion 자동 업로드는 매일 cron 스케줄로 운영하기로 했고, 아직 OAuth
  인증 전 단계다. 세션 재시작 → `/mcp` → Notion 로그인 순서로 이어간다.
- Ponytail 플러그인은 아직 설치하지 않았다. owner 확인 후 설치 여부
  결정.
- Milestone 3(계정 보안 기능: 재연결, 마지막 로그인 수단 해제 방지,
  탈퇴)은 다른 마일스톤을 먼저 진행한 뒤 가장 마지막에 진행하기로
  결정했다. `AGENTS.md`/`prd_v4.md`의 "다음 마일스톤" 순서와 다르므로,
  다음 작업 시작 시 이 순서 변경을 다시 확인한다.

## 학습 기록 — 2026-10-13 (Milestone 4 — Native blog)

### 오늘 한 것

1. Ponytail 플러그인(5.2.0)을 설치했고, `ccusage statusline`으로 상태줄에
   토큰 사용량이 표시되는 것을 확인했다.
2. `m4-blog` 브랜치에서 Milestone 4를 구현했다.
   - `BlogPost` 모델: 제목, slug(고유), 요약, 본문, 상태(초안/발행됨),
     공개 범위(공개/비공개), `published_at`.
   - 공개 화면 `/blog/`, `/blog/<slug>/`.
   - 관리 화면 `/blog/drafts/`: 목록, 새 글, 수정, 발행, 초안으로 되돌리기.
   - 본문 렌더링 필터 `render_body`, admin 등록, 대시보드 "글 관리" 링크.
3. 테스트 12개를 추가해 전체 24개가 PostgreSQL에서 통과했다.
   `manage.py check`와 `makemigrations --check`도 통과했다.
4. owner가 브라우저에서 직접 글 작성과 발행을 확인하고 Milestone 4를
   승인했다.

### 배운 내용

- 공개/비공개 경계는 템플릿에서 숨기는 것이 아니라 queryset에서 강제한다.
  공개 뷰는 `BlogPost.objects.public()` 하나만 사용하고, 이 메서드가
  `status=published`와 `visibility=public`을 함께 요구한다.
- 회원가입이 열려 있으면 "로그인한 사용자"와 "owner"는 다르다.
  `login_required`만으로는 가입자 누구나 공개 블로그에 글을 올릴 수 있어서
  `is_staff` 확인을 추가했다.
- `user_passes_test`는 조건 실패 시 로그인 화면으로 보내는데, 로그인 화면이
  이미 로그인한 사용자를 `next`로 되돌리면 redirect loop가 된다. 권한
  부족은 `PermissionDenied`(403)로 처리하는 것이 맞다.
- 다른 사용자의 글에 대한 접근은 403이 아니라 404로 응답한다.
  `get_object_or_404(BlogPost, pk=pk, author=request.user)`처럼 조회 조건에
  소유자를 넣으면 글의 존재 여부도 드러나지 않는다.
- 상태를 바꾸는 동작(발행)은 `require_POST`와 CSRF 토큰으로 보호한다.
  GET 링크로 만들면 링크 미리보기나 크롤러가 발행을 실행할 수 있다.
- URL 패턴은 위에서부터 매칭되므로 `drafts/`를 `<slug:slug>/`보다 먼저
  둔다. 그래도 slug가 `drafts`인 글은 접근할 수 없게 되므로 폼에서
  예약어로 막았다.
- 사용자 입력을 HTML로 렌더링할 때는 먼저 전부 escape하고, 허용할 구조만
  직접 만든다. `mark_safe`는 escape가 끝난 조각에만 쓴다.
- `on_delete=PROTECT`는 참조하는 데이터가 있으면 삭제 자체를 막는다.
  `CASCADE`는 User를 지울 때 글까지 지우므로, 정책이 정해지기 전에는
  `PROTECT`가 안전하다.
- PostgreSQL은 `DESC` 정렬에서 `NULL`을 앞에 둔다. `-published_at` 정렬에서
  초안(`published_at`이 NULL)이 관리 목록 맨 위에 오는 이유다.

### 기억할 것

- 글을 쓰려면 staff 계정이 필요하다. `createsuperuser`로 만들거나 admin에서
  staff 권한을 부여한다.
- 본문은 ``` 코드 블록만 지원한다. 제목, 링크, 굵은 글씨가 필요해지면
  Markdown 라이브러리와 HTML sanitizer를 함께 도입한다.
- slug는 직접 입력하며 영문, 숫자, `-`, `_`만 허용된다.
- 태그, 글 삭제 화면, `source_submission`/`source_analysis` 연결은 아직
  없다. 연결 필드는 Milestone 5·9에서 추가한다.
- 탈퇴 시 글 처리 정책(삭제 또는 익명화)은 Milestone 3에서 결정한다.
- 다음은 Milestone 5(Activity/Coding 도메인)이며 외부 연동이 필요 없다.
  Milestone 3은 계속 마지막 순서다.

## 학습 기록 — 2026-10-14 (Milestone 4.5a·5 — 블로그 에디터·댓글, 코딩 도메인)

### 오늘 한 것

1. 폰에서 진행 상황을 보도록 Remote Control을 연결했다. 푸시 알림은
   `/config`에서 모바일 푸시가 꺼져 있어 아직 전송되지 않는다.
2. `prd_v5.md`를 만들었다. Milestone 4.5a(에디터·첨부·댓글)를 5 앞에
   추가하고, 블로그 UI 정리는 Milestone 10으로, Milestone 3 잔여 작업은
   마지막으로 정리했다. `AGENTS.md`도 v5를 기준으로 바꿨다.
3. Milestone 4.5a를 구현했다.
   - Quill 2 에디터(CDN): 정렬, 이미지, 📎 파일 첨부, 코드 블록.
   - 본문을 HTML로 저장하고 `nh3`로 sanitize, 기존 평문 본문은
     마이그레이션으로 변환.
   - 첨부 업로드(staff 전용, 10MB, 확장자 허용 목록, 이미지 EXIF 제거).
   - 회원·비회원(닉네임 + 비밀번호) 댓글, honeypot, 삭제 권한.
4. Milestone 5를 구현했다.
   - `ActivityEvent`, `CodingSubmission`, `CodeAnalysis` 모델.
   - `/coding/`(목록·직접 기록·상세), `/activity/`(타임라인).
   - `owner_required`를 `common/`으로 옮김.
5. 헤드리스 브라우저(Playwright)로 폰 화면 크기에서 직접 조작해 확인하고
   스크린샷을 폰으로 받았다. 그 과정에서 버그 2개를 고쳤다.
   - 첨부 후 커서가 이동하지 않아 파일 링크가 사진 앞에 들어가던 문제.
   - 긴 문제 URL이 폰 화면 밖으로 넘치던 문제.
6. 브랜치 정책을 바꿨다. Claude가 진행·테스트한 작업은 `update`에
   커밋·push하고, owner가 직접 확인한 것만 `main`에 합친다. 테스트는
   전체 45개가 통과했다.

### 배운 내용

- 에디터가 만든 HTML을 그대로 보여 주면 XSS가 된다. 허용 목록 방식
  sanitizer(`nh3`)로 허용한 태그·속성·class만 남기고, 나머지(`<script>`,
  `onclick`, `style`, `javascript:`/`data:` URL)는 지운다.
- sanitize는 폼이 아니라 `BlogPost.save()`에서 한다. 폼, admin, 앞으로
  LLM이 만드는 자동 초안이 모두 같은 검사를 지나가게 하기 위해서다.
  템플릿의 `|safe`는 이 검사를 전제로만 쓴다.
- 업로드 파일은 사이트와 같은 도메인에서 서빙되므로 `.html`·`.svg`를
  받으면 그 안의 스크립트가 실행될 수 있다. 확장자 허용 목록으로 막는다.
- 폰 사진의 EXIF에는 GPS 위치가 들어 있다. Pillow로 다시 인코딩하면
  EXIF가 빠지는데, 회전 정보도 EXIF에 있어서 `ImageOps.exif_transpose`로
  회전을 먼저 적용해야 사진이 눕지 않는다.
- 비회원 댓글 비밀번호도 `make_password`로 해시해서 저장하고
  `check_password`로 비교한다. 평문으로 저장하면 안 된다.
- `hidden` 처리한 `required` textarea는 브라우저가 submit 자체를 막는다.
  유효성 검사가 submit 이벤트보다 먼저 일어나기 때문이다. 서버 검증은
  그대로 두고 브라우저 쪽 `required`만 끈다.
- Django `forms.CharField`는 기본으로 앞뒤 공백을 지운다(`strip=True`).
  소스 코드를 그대로 보존하려면 `strip=False`가 필요하다.
- 조건부 `UniqueConstraint`(`condition=~Q(commit_sha='')`)를 쓰면 커밋이
  있는 데이터만 중복을 막고, 직접 입력은 자유롭게 둘 수 있다.
- 두 모델을 함께 만드는 함수는 `transaction.atomic`으로 묶는다. 중간에
  실패하면 먼저 만든 `ActivityEvent`까지 롤백된다.
- 앱끼리 서로 import하면 순환 의존이 생기기 쉽다. 여러 앱이 쓰는 코드는
  `common/`에 두고, 의존 방향은 `coding → activity`처럼 한쪽으로만 둔다.
- sudo 없이도 `apt-get download` + `dpkg -x`로 라이브러리를 사용자 폴더에
  풀고 `LD_LIBRARY_PATH`로 지정해 쓸 수 있다.
- push는 커밋을 올리는 동작이라 커밋 없이 push할 수 없다. 확정 전 작업을
  백업하려면 별도 브랜치에 커밋해서 push한다.

### 기억할 것

- `main` = owner가 확인한 것, `update` = Claude가 진행·테스트한 것.
  `update`를 `main`에 합치는 것은 owner가 직접 확인한 뒤에 한다.
  현재 `update`에는 4.5a(`6fee01e`)와 5(`b6b5556`)가 있다.
- 블로그 화면은 아직 기본 HTML이다. UI 정리는 Milestone 10에서 한다.
- 남은 shortcut: 비회원 비밀번호 시도 횟수 제한 없음(Milestone 10),
  글에서 지운 첨부 파일이 디스크에 남음(Milestone 11).
- 다음은 Milestone 6(Celery)이고 Redis가 필요하다. PC에서
  `sudo apt install -y redis-server`로 설치하거나, sudo 없이 사용자
  폴더에 풀어서 띄우는 방법 중 하나를 고른다.
- 폰으로 푸시 알림을 받으려면 PC에서 `/config`로 모바일 푸시를 켠다.

## 학습 기록 — 2026-10-15 (Milestone 6 — Celery foundation)

### 오늘 한 것

1. Milestone 6 시작 전에 Redis, 브로커, Celery의 역할을 공부했다.
2. PC에 Redis 8.0.5를 설치했고(`sudo apt install redis-server`), AOF 영속화
   (`appendonly yes`)를 켰다. venv에 빠져 있던 `redis` Python 패키지도 설치했다.
3. `common.ProcessingRun`을 추가했다. 백그라운드 작업 1건의 상태, 시도 횟수,
   시작·종료 시각, 실패 사유를 PostgreSQL에 남긴다.
4. 코딩 제출 상세 화면에 "AI 분석 요청" 버튼과 "처리 기록" 목록을 추가했다.
   요청은 작업 쪽지를 큐에 넣고 바로 응답하고, 실제 처리는 Celery 워커가 한다.
   LLM은 Milestone 8에서 연결하므로, 지금은 "LLM provider is not configured"
   실패가 기록되는 것이 정상이다.
5. owner 장애 테스트에서 결함 2개를 찾아 고쳤다(아래 "디버깅 기록").
6. Milestone 4.5a, 5, 6을 owner가 확인했고 `update`를 `main`에 fast-forward로
   병합했다. 테스트 50개 통과.

### 배운 내용

- **Redis**는 RAM에 데이터를 저장하는 키-값 저장소다. 쓰임새는 크게 두 가지다.
  하나는 캐시(자주 읽는 DB 데이터를 복사해 둠, "윤활제" 역할)이고, 다른 하나는
  브로커(할 일 쪽지 보관, "주문표 꽂이" 역할)다. 이 프로젝트는 브로커로만 쓴다.
- **브로커**는 일을 시키는 쪽(생산자, Django)과 일을 하는 쪽(소비자, 워커) 사이에서
  메시지를 맡아 두는 중간 보관소다. 하는 일은 받기, 보관, 넘기기뿐이다.
  양쪽을 분리하는 장치이지 백업 장치가 아니다. 브로커 자체도 단일 장애점(SPOF)이 된다.
- 비동기로 처리하면 브로커의 "속도"는 거의 의미가 없다. 큐가 필요한 진짜 이유는
  "대기 시간"이다. GitHub webhook은 응답을 약 10초까지만 기다리고, LLM 호출은
  수십 초가 걸린다.
- Celery를 쓰는 가치는 재시도, 실패 처리, 예약 실행 같은 기능에 있다. Redis는
  Celery를 돌리는 연료통일 뿐이다. Celery를 안 쓰면 Redis도 필요 없다
  (대안: PostgreSQL 상태 컬럼 + 간단한 워커).
- 브로커 안정성을 높이려면 직렬 연결이 아니라 병렬 복제(Replication + Sentinel)를
  쓴다. 직렬로 연결하면 장애 지점이 오히려 늘어난다. 이 프로젝트는 원본이
  PostgreSQL에 있으니 Redis 1대 + AOF로 충분하다.
- 세 프로그램의 역할: Redis(`systemctl`로 관리하는 OS 서비스), Django
  (`runserver`), Celery 워커(`celery -A config worker -l info`, `-l`은 소문자 L).

### 디버깅 기록 — Redis를 끄면 기록이 "대기"로 남던 문제

- **증상**: Redis를 끈 상태에서 분석 요청을 하면 노란 오류 화면이 뜨고, 기록은
  "대기"로 남아 영원히 처리되지 않았다. Redis를 다시 켜도 `runserver`를
  재시작해야만 복구됐다.
- **원인**: `.env`의 `CELERY_RESULT_BACKEND` 때문이었다. 이 값이 있으면 Celery는
  작업을 브로커에 넣기 **전에** 결과 저장소(같은 Redis)에 먼저 구독 연결을 한다.
  여기서 `RuntimeError`가 났는데, 코드는 브로커 오류(`OperationalError`)만
  대비하고 있었다. 또 Celery는 `settings.py`보다 **환경 변수**를 먼저 읽어서,
  설정 파일에서 지워도 `.env`에 남은 값이 계속 쓰였다. 결과 저장소 연결은 한 번
  고장 나면 다시 연결하지 않아서("must be restarted") 재시작이 필요했다.
- **해결**: 큐 등록이 어떤 이유로든 실패하면 기록을 "Enqueue failed"로 남기고 로그를
  찍게 했다. 그리고 `CELERY_TASK_IGNORE_RESULT = True`로 결과 저장소를 아예 쓰지
  않게 했다(결과는 PostgreSQL에 저장). 이제 Redis를 껐다 켜도 재시작 없이 복구된다.
- **교훈**: 내가 만든 재현 환경이 실제와 달랐다(브로커만 끄고 결과 저장소는 살아
  있었음). 그래서 처음에는 재현에 실패했다. 실제 traceback을 받아서야 원인이
  보였다.

### 기억할 것

- 개발할 때는 터미널 2개(runserver, worker)와 Redis 서비스가 필요하다.
  `redis-cli ping` → `PONG`이면 Redis가 켜진 상태다.
- 정상 상태 확인: 평상시 = ImproperlyConfigured(LLM 미설정), 워커 꺼짐 = 대기,
  Redis 꺼짐 = Enqueue failed.
- 재시도(backoff)는 실패 유형을 아는 Milestone 7·8에서 붙인다.
- 다음은 Milestone 7(GitHub webhook)이다. 시작하면 Checkpoint B에서 실제 저장소,
  풀이 파일 예시, webhook 수신 주소(터널)를 정해야 한다.

## 학습 기록 — 2026-10-20 (Milestone 11 — 첫 배포: Docker·EC2·DuckDNS·HTTPS)

### 오늘 한 것

1. learning log에 평문으로 남아 있던 로컬 계정 비밀번호를 지웠다. Git 첫 커밋
   기록에는 남아 있으므로, 히스토리를 고쳐 쓰는 대신 비밀번호를 바꾸기로 했다
   (`manage.py changepassword arthur0626`).
2. 계획을 바꿨다(`prd_v5.md` "2026-10-20 결정 사항"). 배포를 Milestone 7 앞으로
   당겼다. Milestone 7은 7a(사이트에 붙여넣은 풀이를 서버가 GitHub에 커밋, 필수)와
   7b(GitHub push webhook 수신, 시간 되면)로 나눴다. 풀이 저장소는
   `arthur0626/2026-Coding-Test`다. CI는 하고, Kubernetes와 자동 배포(CD)는 하지
   않으며, Terraform은 11/09 이후에 검토한다.
3. 운영용 Docker 묶음을 만들었다. `Dockerfile`(gunicorn), `compose.prod.yml`
   (web·worker·postgres·redis·caddy), `deploy/Caddyfile`(HTTPS 자동 발급,
   정적·업로드 파일 제공). 로컬에서 먼저 띄워 검증했다(쉴 때 전체 메모리 약 310MB).
4. AWS에 가입해 MFA와 월 $10 예산 알림을 설정했다. 서울 리전에 EC2 `ProjectJ`
   (Ubuntu 26.04, t3.micro, 디스크 20GB)를 만들고, 탄력적 IP를 붙이고,
   swap 2GB를 추가했다.
5. 무료 도메인 `arthur0626.duckdns.org`를 만들어 서버 IP에 연결했다.
6. 서버에 Docker를 설치하고, 코드를 받고, `.env`를 서버에서 직접 작성한 뒤
   `docker compose -f compose.prod.yml up -d --build`로 실행했다.
   https://arthur0626.duckdns.org 이 Let's Encrypt 인증서로 열렸다.
7. Kakao 콘솔의 REST API 키에 운영 redirect URI를 추가했고, 운영 사이트에서
   Kakao 로그인이 동작했다.

### 배운 내용

- **EC2와 Docker는 층이 다르다.** EC2는 빌린 컴퓨터(주방)이고, Docker는 그 위에서
  앱을 포장해 돌리는 도구(밀키트)다. 같은 이미지라서 로컬에서 확인한 스택이
  서버에서도 그대로 돈다. 서버 OS를 WSL과 같은 Ubuntu 26.04로 맞추니 Docker
  버전(29.1.3)도 똑같이 설치됐다.
- 만드는 것은 윈도우 프로그램이 아니다. 개발 환경인 WSL 자체가 Ubuntu
  리눅스이고, 컨테이너 내부도 리눅스다. 서버로 리눅스를 쓰는 이유는 무료,
  가벼움, 업계 표준이기 때문이다.
- **보안 그룹**은 기본이 "전부 차단"이고, 연 포트만 들어올 수 있다. SSH(22)는
  내 IP만, HTTP(80)·HTTPS(443)는 전체에 열었다. 80번은 http → https 이동과
  인증서 발급에 필요하다.
- **키 페어**는 내 PC에서 서버 터미널에 들어갈 때(SSH)만 쓴다. 서버에는
  자물쇠(공개 키)가 있고, 나는 열쇠(`.pem`, 개인 키)를 가진다. 열쇠 파일은
  `chmod 600`이어야 SSH가 받아 준다.
- **탄력적 IP**는 재시작해도 바뀌지 않는 고정 주소다. 도메인(A 레코드)이 이
  IP를 가리킨다. 2024년부터 공인 IPv4는 연결 여부와 상관없이 시간당 과금된다.
- 요금: 인스턴스는 켜져 있는 동안 초 단위로 과금된다. 중지하면 서버 요금은
  멈추지만 디스크와 IP 요금은 남는다. 완전히 그만둘 때는 인스턴스 종료와
  탄력적 IP 릴리스를 둘 다 해야 한다. 사양(micro ↔ small)은 중지 후 바꿀 수
  있고, OS와 리전은 새로 만들어야 한다.
- **Caddy**는 리버스 프록시다. 바깥의 HTTPS 요청을 받아 gunicorn(web:8000)으로
  넘긴다. Nginx와 달리 certbot 없이 Let's Encrypt 인증서를 자동으로 발급하고
  갱신한다. Django는 프록시 뒤에 있으므로 `X-Forwarded-Proto` 헤더로 원래
  요청이 https였는지 판단한다(`SECURE_PROXY_SSL_HEADER`).
- 운영에서는 `runserver` 대신 gunicorn(WSGI 서버)을 쓴다. `runserver`는
  개발용이라 성능과 보안이 운영에 맞지 않는다.
- **코드, 데이터, 설정은 따로 움직인다.** 코드는 Git으로 서버에 가지만, 데이터
  (DB, 업로드 파일)와 설정(`.env`)은 가지 않는다. 일부러 그렇게 한다. 운영 DB는
  빈 상태로 시작하고, `.env`는 환경마다 값이 달라야 하며(DEBUG, 도메인, DB
  비밀번호), 비밀 값은 공개 저장소에 올리면 안 된다. 이것을 12-Factor App의
  Config 원칙이라고 한다.
- Django의 `migrate`는 데이터를 옮기는 것이 아니라 테이블 구조를 만드는
  것이다. 서버에서는 web 컨테이너가 시작할 때 자동으로 실행된다.
- Kakao 콘솔은 2025년 개편 후 설정이 앱 키별로 나뉘었다. 서버 로그인
  (allauth)은 REST API 키의 리다이렉트 URI만 등록하면 된다. 예전 "사이트
  도메인"은 JavaScript SDK 도메인으로 바뀌었고 이 프로젝트에는 필요 없다.
- 도메인: 무료(DuckDNS)와 유료는 HTTPS, OAuth, webhook 등 기술적으로 같다.
  다른 점은 소유권, 신뢰도와 인상, 일부 회사 방화벽 차단 가능성이다. 나중에
  바꾸려면 `.env` 3개 값과 Kakao redirect URI만 고치면 된다.

### 기억할 것

- 서버 접속: `ssh -i ~/.ssh/ProjectJ.pem ubuntu@3.39.140.204`
- 서버 코드 위치는 `~/devos`이고 현재 `update` 브랜치를 받는다(main 병합 후
  main으로 바꾼다).
- 업데이트 배포: `cd ~/devos && git pull && docker compose -f compose.prod.yml up -d --build`
- 상태와 로그: `docker compose -f compose.prod.yml ps`,
  `docker compose -f compose.prod.yml logs <서비스> --tail 30`
- 운영 DB와 업로드 파일은 아직 백업이 없다. 백업(EBS 스냅샷)을 하기 전에는
  실제 글을 쓰지 않는다.
- 다음(10/21): EBS 스냅샷 백업, 운영 관리자·dev 계정 정리, 사이트 둘러보기
  (글 쓰기, 이미지 업로드), owner 확인 후 `main` 병합. 그다음은 CI와
  Milestone 7a.
