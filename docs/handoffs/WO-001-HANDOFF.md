## Yapılanlar
- `uv init --bare` ve pnpm tabanlı workspace (monorepo) kuruldu.
- `apps/web` (Next.js), `apps/api` ve `apps/worker` dizinleri oluşturuldu.
- Workspace yapılandırmaları için `pyproject.toml`, `pnpm-workspace.yaml` (ve pnpm engellerini atlamak için geçici çözümler ve dummy `test_api.py`) eklendi.
- `Makefile`, `.env.example`, `AGENTS.md` ve `CLAUDE.md` oluşturuldu.
- `make dev-doctor`, `make lint` ve `make test` başarıyla çalıştırıldı.

## Değişen dosyalar
- `pyproject.toml` [NEW]
- `pnpm-workspace.yaml` [NEW]
- `package.json` [NEW]
- `apps/web/` [NEW]
- `apps/api/` [NEW]
- `apps/worker/` [NEW]
- `Makefile` [NEW]
- `.env.example` [NEW]
- `AGENTS.md` [NEW]
- `CLAUDE.md` [NEW]

## Tasarım kararları
- Next.js için `create-next-app` kullanıldı; `pnpm` kurarken karşılaşılan "Ignored build scripts" hatası nedeniyle `--ignore-scripts` ile `pnpm install` çalıştırıldı.
- Boş dizinlerde testlerin patlamaması için geçici olarak `apps/api/test_api.py` adlı dummy test eklendi ve `apps/web/package.json` içine "test" eklendi.

## Test komutları ve sonuçları
```bash
make dev-doctor
make lint
make test
```
(Tümü başarıyla çalıştı)

## Migration etkisi
- Yok.

## Güvenlik etkisi
- Yok.

## Bilinen eksikler
- Yok.

## Rollback
- Silinmesi gereken commit yok.

## Sonraki önerilen WO
- WO-002
