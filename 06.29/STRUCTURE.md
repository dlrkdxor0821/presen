# arte · Libi 폴더 구조

> **ABA / 리비(Libi)** — 주행로봇 + 로봇팔(모바일 매니퓰레이터)로 도서관 사서를 돕는 협동로봇.
> 여러 UI 명령을 중앙에서 받아 **배차(누가 할지) + 교통협상(주행 중 충돌 회피)** 으로 멀티 로봇을 지휘하는 **FMS(관제) 시스템**의 전체 구조(스켈레톤).

---

## 📂 전체 트리

```
arte_folder_structure/
│
├── app/                            # 사용자 대면 애플리케이션 (프론트엔드)
│   └── libi_gui/                   #   리비 운영자용 관제 GUI
│
├── controller/                     # 로봇 탑재 컨트롤러 (로봇 1대 = 도메인 1개)
│   ├── libi_drive_controller/      #   주행 컨트롤러 — fleet은 오직 Drive와만 통신
│   │   └── src/                    #     drive_node 등 주행 노드 (nav2/slotcar 백엔드)
│   └── libi_handy_controller/      #   로봇팔(Handy) 컨트롤러 — Drive가 지휘
│
├── libi_fleet/                     # ★ FMS 두뇌 (관제 코어, C++) — 배차 + 교통
│   ├── maps/                       #   맵 데이터 (navgraph · building.yaml · .pgm)
│   └── src/
│       ├── libi_fleet/             #     FMS 코어 패키지 (fleet_node · navgraph · plugins)
│       └── libi_fleet_msgs/        #     인터페이스 패키지 (srv/msg/action 계약)
│
└── service/                        # 백엔드 서비스 계층 (중앙관제 + 부가 서비스)
    ├── ABA_service/                #   중앙관제 입구 (FastAPI ↔ ROS2 브리지)
    ├── ABA_web_service/            #   웹 서비스 (브라우저 대면)
    │   ├── librarian_browser/      #     사서용 웹 — 로봇 호출/관제/태스크 발행
    │   └── library_member_browser/ #     이용자용 웹 — 책 안내/배달 요청
    └── ai_service/                 #   AI 서비스 (도서 추천·음성/대화·비전)
```

> 15 directories — 아직 **뼈대(스켈레톤)** 상태.

---

## 🧭 데이터 흐름

```
[app / ABA_web_service]  ── HTTP ──▶  [service/ABA_service]  ── ROS2(SubmitTask) ──▶  [libi_fleet]
   사서·이용자 UI                        FastAPI 중앙관제 입구                          FMS 두뇌(배차+교통)
                                                                                          │
                                                                          ROS2(PathRequest / action)
                                                                                          ▼
                                                                              [controller] Drive ──▶ Handy(팔)
```

- **fleet ↔ Drive only** : fleet은 로봇당 Drive와만 통신. 팔(Handy)은 Drive가 지휘.
- **배차·교통은 pluginlib 전략** : config / 콘솔 드롭다운으로 런타임 교체.

---

## 📑 폴더별 역할

| 레이어 | 폴더 | 역할 |
|---|---|---|
| **프론트엔드** | `app/libi_gui` | 리비 운영자용 관제 GUI |
| **컨트롤러** | `controller/libi_drive_controller` | 주행 컨트롤러 (nav2/slotcar 백엔드) — fleet과 직접 통신 |
| | `controller/libi_handy_controller` | 로봇팔(Handy) 컨트롤러 — Drive가 지휘 |
| **★ 관제 코어** | `libi_fleet/src/libi_fleet` | FMS 본체 — `fleet_node`(상태머신) · `navgraph`(Dijkstra) · `plugins`(배차/교통) |
| | `libi_fleet/src/libi_fleet_msgs` | 인터페이스 계약 — `SubmitTask`·`SetPlugins`(srv), `Navigate`·`PerformAction`(action), `RobotState`·`TaskState`(msg) |
| | `libi_fleet/maps` | 맵 데이터 — navgraph · building.yaml · .pgm |
| **백엔드** | `service/ABA_service` | 중앙관제 입구 — FastAPI ↔ rclpy 브리지, 태스크 접수/거절 |
| | `service/ABA_web_service/librarian_browser` | 사서용 웹 — 로봇 호출·관제·태스크 발행 |
| | `service/ABA_web_service/library_member_browser` | 이용자용 웹 — 책 안내·배달 요청 |
| | `service/ai_service` | AI 서비스 — 도서 추천·음성/대화·비전 |

> `app/libi_gui`, `ABA_web_service`, `ai_service`, `*_browser` 의 세부 역할은 **폴더명 기반 추정** — 실제 의도와 다르면 조정 필요.
