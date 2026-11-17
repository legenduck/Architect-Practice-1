# 수업 전 준비

수강생은 Codex CLI에 미리 로그인하고, 강사는 전원을 원본 저장소의 collaborator로 등록합니다. 수강생 PC에서 Git 인증과 `user.name`·`user.email`도 설정해 둡니다. 시작 도구는 계정 설정을 입력받지 않습니다.

## 자동 채점과 전체 결과

`main`에 이 변경을 반영한 후 저장소 Settings → Pages → Source를 **GitHub Actions**로 선택합니다. Actions에서 **Grade practice submissions**를 한 번 실행해 빈 결과 화면을 준비합니다. 포크에서는 Actions도 먼저 활성화합니다. `github-pages` 환경의 배포 브랜치 규칙에 `students/*`를 허용합니다.

결과 게시 작업은 저장소 전용 SSH 배포 키를 사용합니다. Settings → Deploy keys에 쓰기 가능한 공개 키를 등록하고, 대응하는 개인 키를 Actions secret `RESULTS_DEPLOY_KEY`에 저장합니다. `results` 갱신 제한 규칙에는 Deploy keys 예외를 허용하되, 삭제·강제 push 금지 규칙은 별도로 유지합니다. `main` 보호 규칙에는 배포 키 예외를 추가하지 않습니다. 포크에서도 이 키와 규칙을 준비한 후 워크플로를 실행합니다.

이후 `students/*`의 제출 ZIP push가 자동 채점을 시작합니다. 5분 주기 수집과 수동 실행도 지원합니다. 수강생 코드와 테스트는 네트워크·인증 정보가 없는 일회용 컨테이너에서 실행합니다. 원본 테스트, 제출 테스트, 운영 규정에서 작성한 쿠폰 검사 24개를 통과하면 `results` 브랜치에 채점 영수증을 기록하고 GitHub Pages를 갱신합니다. 기존 외부 채점기를 대체하는 별도 구현이므로 수업 전에 규정과 검사 범위를 검토합니다.

전체 화면은 참가자·실행 순으로 표시하며, 통과한 동일 조건의 기본 실행과만 절감률을 계산합니다. 채점 파일의 제출 blob과 소스 체크섬이 일치해야 `python lab.py sync`에 반영됩니다. 변경하지 않은 제출은 재채점하지 않습니다.

포크로 운영하면 준비된 각 PC의 `config.json`에서 `repository`도 해당 포크 URL로 맞춥니다. 전체 결과 주소는 `https://<소유자>.github.io/Architect-Practice-1/`입니다. 원본 저장소에는 이 PR 병합과 위 설정이 필요합니다.

## 공통 환경

Python 3.10 이상, Git, 수업용 Codex CLI를 설치하고 각 PC에서 실행합니다.

```bash
git clone https://github.com/legenduck/Architect-Practice-1.git
cd Architect-Practice-1
python start.py doctor
```

Windows에서는 `py -3`, macOS/Linux에서는 `python3`를 사용할 수 있습니다. 모델은 `gpt-5.6-terra`, 추론 강도는 `medium`으로 고정되어 있어 별도 모델 설정이 필요하지 않습니다. 이전 `config.json`의 모델·추론 값도 실행 시 고정값으로 대체됩니다. CLI 버전·전역 지침은 수업 전체에서 동일하게 맞춥니다. 기존 `--prepare` 명령은 패키지와 작업 폴더를 미리 준비하는 용도로 유지하지만 일반 시작에는 필요하지 않습니다. 참가자 번호를 미리 넣으려면 `--participant p01`을 추가합니다. `config.json`과 `.venv`는 PC별로 준비하며 Git에 포함되지 않습니다.

## 준비 확인

`doctor`는 실행 도구·Codex 로그인·샌드박스 파일 입출력과 테스트만 확인합니다. 강사용 모델 설정이나 GitHub 제출 권한·채점 결과 수신 경로는 확인하지 않습니다. 참가자 번호 입력, 브랜치 전환, 커밋, push, 모델 호출은 하지 않습니다. 시작 도구는 고정 모델 설정을 `config.json`에 저장합니다. 결과는 짧게 표시하고 상세 오류는 `doctor.log`에 남깁니다. 중앙 채점 준비는 GitHub 제출 기능을 사용할 때 별도로 진행합니다.

GitHub 등록과 PC의 Git 인증은 별도이므로 실제 수강생 계정으로 점검합니다. 샌드박스 오류가 나면 해당 PC의 실행 환경을 정비합니다. 모델 접근 권한과 중앙 채점 동작은 모델을 호출하지 않는 `doctor`만으로 확인할 수 없으므로, 배포 전에 기본 지침 실행 → 제출 → 채점 수신을 한 번 완료합니다.

## Windows 샌드박스 1385 오류

이 실습의 Windows 기본값은 `unelevated`입니다. `windows.sandbox` 설정과 `codex sandbox --permission-profile` 명령을 지원하는 Codex CLI를 준비합니다. 설정에 `windows_sandbox` 항목이 없던 기존 PC에도 업데이트 후 기본값이 적용됩니다. 이미 다른 방식을 명시한 PC에서는 다음 명령으로 변경합니다.

```powershell
python start.py doctor --windows-sandbox unelevated
```

실습 폴더의 `config.json`에 `"windows_sandbox": "unelevated"`가 저장됩니다. 시작 메뉴와 `lab.py run`은 이 선택을 읽어 Windows에서 Codex에 `-c windows.sandbox="unelevated"`를 전달합니다. `doctor`도 같은 설정으로 실제 파일 읽기·쓰기와 테스트를 점검합니다. 관리 정책을 읽는 CLI 옵션이 제공되면 점검에도 적용하며, 실패하면 실행을 중단합니다. 이 설정은 GitHub 제출 권한과는 별개입니다.

1385는 Windows가 샌드박스 실행 계정에 필요한 로그온 권한을 허용하지 않을 때 발생합니다. `unelevated`는 현재 Windows 사용자의 제한된 토큰을 사용하는 방식으로, `elevated`보다 네트워크 격리가 약하고 읽기 금지 경로를 지원하지 않습니다. 조직 정책이 금지하는 경우에는 관리자의 환경 설정이 필요합니다. 샌드박스를 끄거나 관리자 권한으로 과제를 실행하는 옵션은 추가하지 않습니다. [Codex 공식 Windows 샌드박스 안내](https://learn.chatgpt.com/docs/windows/windows-sandbox#configure-a-legacy-fallback)를 참고하세요.

기존 방식은 `python start.py doctor --windows-sandbox elevated`, Codex 자체 설정을 따르는 방식은 `python start.py doctor --windows-sandbox default`로 선택합니다. 명시적으로 선택한 Windows 샌드박스 방식은 실행 조건에 기록하므로, 방식을 바꿨다면 기본 지침 실행부터 다시 측정합니다. Linux와 macOS에서는 이 Windows 설정이 적용되지 않습니다.

## 수강생 흐름

`start.bat` 또는 `start.command` 실행 → 최초 참가자 번호 입력 → 메뉴에서 실습을 반복합니다. 메뉴는 실행 후에도 유지되며, 제출 후 채점을 기다리지 않고 다음 실험을 진행할 수 있습니다. 제출 실패는 같은 기록으로 재시도합니다. 실습 중에는 로그인이나 Git 계정 설정을 진행하지 않습니다.

수업 안내에는 [수강생 사용 시나리오](student-workflow.md)를 배포합니다. 실제 메뉴 순서, 지침 수정 요청 예시, 기법 기록과 결과 비교, 오류 대응을 설명합니다.

회귀 테스트: `python -m unittest discover -s tests_lab -v`. 대체 CLI와 로컬 Git 저장소로 실행 흐름을 검증하며, 배포할 OS와 실제 모델·중앙 채점 환경은 별도로 확인합니다.
