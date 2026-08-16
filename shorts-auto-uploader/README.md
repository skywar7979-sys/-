# shorts-auto-uploader

큐에 등록한 짧은 문구를 세로형(1080x1920) 영상으로 자동 생성하고, YouTube Shorts /
Instagram Reels / TikTok에 자동으로 게시하는 프로그램입니다. GitHub Actions로
매일 정해진 시간에 큐에서 아직 올리지 않은 항목을 하나씩 꺼내 자동 업로드합니다.

## 동작 방식

1. `config/content_queue.yaml`에 올릴 항목(제목/스크립트/해시태그)을 등록
2. `src/generate.py`가 TTS 음성 + 텍스트 오버레이로 mp4를 렌더링
3. `PLATFORMS`(또는 항목별 `platforms`)에 지정된 플랫폼에 업로드
4. 업로드에 성공한 항목의 id를 `state.json`에 기록해 재업로드 방지
5. `.github/workflows/shorts_auto_upload.yml`이 매일 큐를 확인해 다음 항목을 자동 게시

## 로컬 실행

```bash
cd shorts-auto-uploader
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 값 채우기

python -m src.main generate   # 렌더링만 (업로드 없음)
python -m src.main run        # 렌더링 + 업로드 + state.json 기록
```

## 플랫폼별 사전 준비 (필수 — 코드만으로는 동작하지 않습니다)

각 플랫폼은 실제 계정 인증이 필요합니다. 아래 절차는 플랫폼 쪽에서 직접 처리해야
하며, 앱 심사가 필요한 경우 수일이 걸릴 수 있습니다.

### YouTube
1. Google Cloud Console에서 프로젝트 생성 → YouTube Data API v3 활성화
2. OAuth 클라이언트(유형: Desktop) 생성 후 `config/youtube_client_secret.json`로 저장
3. 로컬에서 1회 실행해 토큰 발급: `python -m src.oauth_bootstrap youtube`
   (브라우저 동의 화면이 뜨고, 완료되면 `config/youtube_token.json` 생성)
4. 두 JSON 파일 내용을 GitHub 저장소 Secrets에 각각
   `YOUTUBE_CLIENT_SECRET_JSON`, `YOUTUBE_TOKEN_JSON`으로 등록

### Instagram (Reels)
- Instagram 프로페셔널(비즈니스/크리에이터) 계정을 Facebook 페이지에 연결
- `instagram_content_publish` 권한이 있는 장기 액세스 토큰 발급
- Graph API는 영상을 공개 HTTPS URL에서 가져가므로, 렌더링한 파일을 임시로
  올려둘 퍼블릭 스토리지(S3 등)가 별도로 필요합니다 — `src/platforms/instagram.py`의
  `_host_video()`에 해당 업로드 로직을 연결하세요.
- Secrets: `IG_BUSINESS_ACCOUNT_ID`, `IG_ACCESS_TOKEN`, `PUBLIC_VIDEO_HOST_UPLOAD_URL`

### TikTok
- TikTok for Developers에서 앱 등록 후 Content Posting API 사용 승인 신청
  (심사 필요, 승인 전에는 이 경로가 동작하지 않습니다)
- 발급된 액세스 토큰을 Secrets `TIKTOK_ACCESS_TOKEN`, `TIKTOK_OPEN_ID`로 등록

## GitHub Actions 자동화

- 저장소 Settings → Secrets and variables → Actions에서 위 Secrets를 등록
- Settings → Variables에서 `PLATFORMS` 값 설정 (예: `youtube` 또는 `youtube,instagram`)
- 기본 스케줄은 매일 09:00 KST(`0 0 * * *`, UTC 기준)이며 `workflow_dispatch`로 수동 실행도 가능
- 업로드 성공 시 워크플로우가 `state.json`을 커밋해 다음 실행에서 같은 항목을 건너뜁니다

## 제한 사항

- 배경은 단색 + 텍스트로만 구성된 최소 템플릿입니다. 실제 배경 영상/이미지를 쓰려면
  `src/generate.py`의 `ColorClip`을 `ImageClip`/`VideoFileClip`으로 교체하세요.
- 각 플랫폼 API는 여기서 만든 인증 흐름과 별개로, 계정 소유자가 직접 앱 등록/토큰
  발급을 완료해야 실제로 게시됩니다. 이 저장소만으로는 완전 자동화되지 않습니다.
