# Tekken-Tag2-Patch — 태그2 통합패치 최신 RPCS3 대응판

- 기준 RPCS3: `9b8974d32e73c897a5fcd6bdf69413ca7e436b01` (v0.0.40-20583, 2026-11-12 master)
- 원본 패치: 태그2 2026.11.13-07 (R22, `tag2-20261113-07`, 기준 RPCS3 `7cfe96a1`, 2026-02-11)
- 런타임: 공식 RPCS3와 동일 (Qt 6.12.0, FFmpeg avcodec-63), `runtime_abi = qt612-tag2-rpcs3-master`

## 무엇이 바뀌었나

| 항목 | 처리 |
|---|---|
| 롤백(GGPO)·로비·프레임표·HUD·입력·패치 매니저 등 태그2 전용 기능 | 최신 master 위로 그대로 이식 |
| RSX 셰이더 인터프리터 백포트(PR #18676 등, 24개 파일) | 최신 master에 원본이 이미 포함 → 업스트림 코드 사용 |
| Vulkan 디스크 파이프라인 캐시(태그2 기능) | 업스트림의 공유 파이프 컴파일러 캐시에 연결 (이중 해제 방지) |
| 오버레이 폰트 API 변경 (`set_font(이름,크기)` → `set_font(크기,이름)`) | 태그2 HUD·로비 오버레이 2곳 수정 |
| 설치 무결성 검사 | 유지. 관리 대상 DLL을 최신 구성으로 교체(avcodec-63 등), 해시는 빌드 후 `make_release.py`가 생성 |
| 구 U1 딜레이 실행기 (`rpcs3-u1.exe`) | 제외 (구 Qt 6.10.2 DLL이 필요해 같은 폴더에서 동작 불가). rpcs3.exe의 딜레이/롤백 모드는 그대로 |
| 태그2 GitHub 자동 업데이트 | 꺼짐 (구버전 R20으로 되돌아가는 것 방지) |
| 공식 RPCS3 patch.yml 다운로드 | 원본처럼 계속 차단 (태그2 patch.yml 덮어쓰기 방지) |
| patch.yml | 원본 R20 그대로. 패치 엔진 버전 1.2 동일, 포맷 호환 |
| 기타 이식성 수정 | `0x1e+length` 리터럴, CMake 예외 플래그, GGPO `timeGetTime` 헤더 |

## 검증한 범위

- 머지 영향을 받은 기존 RPCS3 파일 (System.cpp, PPUModule, cellPad, PadHandler, pad_thread, bin_patch, VK 렌더러 등): 리눅스 GCC 13 실제 컴파일 통과
- 태그2 윈도우 전용 소스 전체 (tag2_native_* 13개, GreenGGPO/Host, TTT2LobbyPass, ttt2_framedata, main_window/gs_frame의 태그2 블록): MinGW 헤더로 윈도우 타깃 문법·타입 검사 통과
- **아직 안 한 것: MSVC 실제 빌드, 링크, 실게임 테스트(온라인 롤백 포함).** 반드시 실기 확인이 필요합니다.

## 자동 빌드 (GitHub Actions)

`Actions` 탭 → **Build Tag2 (RPCS3 Windows)** → `Run workflow`.

1. RPCS3 `9b8974d3`을 받아 `port/patches/*.patch`를 `git am --keep-cr`로 적용
2. RPCS3 공식 윈도우 CI와 같은 방식(Qt 6.12.0, LLVM 22.1.8, Vulkan SDK 1.4.341.1, MSVC)으로 빌드
3. `port/make_release.py`로 태그2 패키지 생성 → 아티팩트 `Tag2_RPCS3-latest_R24_xxxxxxxx.zip`

`latest-r24` 같은 `latest-*` 태그(또는 Run workflow의 release_tag 입력)를 푸시하면 같은 빌드를 GitHub 릴리스(사전 릴리스)로도 올립니다.
첫 빌드는 1~2시간 걸리고, 이후에는 ccache 덕분에 빨라집니다.

## 저장소 구성

| 경로 | 내용 |
|---|---|
| `port/patches/` | RPCS3 9b8974d3 위에 적용하는 패치 (R20 이식 + 최신 API 대응 + 런타임/업데이트 정책) |
| `port/make_release.py` | 빌드 폴더 → 태그2 설치 패키지 (`TAG2_NATIVE/release.json` 생성) |
| `r20-data/` | 원본 R20의 `patches/patch.yml`, `GREEN_GGPO_SIMPLE_3F/*`, 그래픽 설정 원복 스크립트, 사용방법 |
| `.github/workflows/build-windows.yml` | 윈도우 자동 빌드 |

## 설치

1. 게임과 RPCS3를 완전히 종료
2. 빌드된 zip을 RPCS3 폴더에 풀어서 덮어쓰기 (게임/펌웨어는 포함되지 않음)
3. RPCS3 → 게임 패치 관리에서 원하는 항목 체크 후 **저장** (`config\patch_config.yml`이 없으면 게임 실행이 막힘)
4. 기존 `config\patch_config.yml`(개인 설정)은 지우거나 남의 파일로 덮어쓰지 마세요

## 로컬 빌드

`port/patches`를 RPCS3 `9b8974d3` 체크아웃에 `git am --keep-cr`로 적용한 뒤 RPCS3 `BUILDING.md`대로 빌드하고,
`python port/make_release.py --source <rpcs3> --build <rpcs3\bin> --tag2-dir r20-data --zip out.zip`으로 패키징합니다.

## 라이선스

RPCS3 및 이 수정분은 GPL-2.0-only입니다. 의존성은 각자의 라이선스를 따릅니다. 비공식 빌드이며 RPCS3 공식 배포판이 아닙니다.
