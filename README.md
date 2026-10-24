# canbly-feed

캔블리(@can_bly_official) 인스타그램 피드 자동 발행 저장소.

- 매주 일요일: Claude Code가 다음 주 7건(홈페이지 5 + 블로그 2)을 만들어 `posts/날짜/`에 올림
- 매일 20:00(한국 시간): GitHub Actions가 그날 게시물을 인스타그램에 발행

## 처음 한 번 설정

저장소 → Settings → Secrets and variables → Actions → New repository secret

| 이름 | 값 |
| --- | --- |
| `IG_USER_ID` | 인스타 비즈니스 계정 ID (숫자) |
| `IG_ACCESS_TOKEN` | Meta 개발자 앱에서 발급한 토큰 (instagram_content_publish 권한) |

## 직접 확인·발행하기

저장소 → Actions → "인스타 자동 발행" → Run workflow
- `date`: 발행할 날짜 (비우면 오늘)
- `dry_run`: `true`면 실제로 올리지 않고 점검만

발행에 실패하면 GitHub가 가입 이메일로 알림을 보낸다. 가장 흔한 원인은 토큰 만료다.
