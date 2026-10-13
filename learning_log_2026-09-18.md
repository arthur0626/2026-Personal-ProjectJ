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

- 실제 웹 화면에서 `arthur0626 / qwer0626` 계정 가입까지 완료하여 회원가입 기능을 확인했다.
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
