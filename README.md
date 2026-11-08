# dsh-moduleapi

Провайдер **Module API** ([moduleapi.pro](https://www.moduleapi.pro/)) для **DeepSeek Harness**.
Модуль API — OpenAI-совместимый шлюз с одним ключом на все модели (DeepSeek, GPT, Claude,
Gemini, Grok и др.).

Плагин активирует штатный мульти-провайдерный адаптер `dsh-llm-pi-ai` маршрутом
`moduleapi` → `https://moduleapi.pro/v1` (OpenAI Chat Completions). Ключ **не хранится в
конфиге** — читается из credential store по референсу `MODULEAPI_API_KEY`.

## Установка

Нужен установленный Node.js — всё остальное подтягивается автоматически.

```bat
cd %USERPROFILE%\.dsh\profiles\desktop

:: 1. прописать плагин в манифест профиля (зависимость + бандл):
node -e "const{readFileSync,writeFileSync}=require('fs');const m=JSON.parse(readFileSync('package.json','utf8'));m.dependencies=m.dependencies||{};m.dependencies['dsh-moduleapi']='github:Skeltx/dsh-moduleapi';m.dsh=m.dsh||{};m.dsh.profile=m.dsh.profile||{};m.dsh.profile.bundles=m.dsh.profile.bundles||[];if(!m.dsh.profile.bundles.includes('dsh-moduleapi'))m.dsh.profile.bundles.push('dsh-moduleapi');writeFileSync('package.json',JSON.stringify(m,null,2)+'\n');console.log('manifest ok')"

:: 2. установить пакет (pnpm подтянется через npx)
npx pnpm@latest install

:: 3. перезапустить DeepSeek Harness — готово.
```

После запуска в выборе модели появится провайдер **Module API** с пятью моделями.

## Ключ

Два варианта:

- **GUI (рекомендуется):** Settings → Models → карточка Module API → поле **API key** —
  ключ сохранится в credential store по референсу `MODULEAPI_API_KEY`.
- **Вручную:** дописать в `~/.dsh/.credentials.yaml`:

```yaml
refs:
  MODULEAPI_API_KEY: sk-ВАШ_КЛЮЧ
```

## CLI-клиент (без Harness)

`client/moduleapi.py` — автономный клиент на чистом Python:

```bat
python client\moduleapi.py check
python client\moduleapi.py ask "Привет" --model deepseek-v4-flash --stream
```

## Модели (v0.1)

| id | название |
|---|---|
| `deepseek-v4-flash` | DeepSeek V4.1 Flash |
| `deepseek-v4-pro` | DeepSeek V4.1 Pro |
| `gpt-5.4` | GPT-5.4 |
| `claude-sonnet-5` | Claude Sonnet 5 |
| `gemini-3.8-flash` | Gemini 3.8 Flash |

Полный каталог (26 моделей) можно подтянуть через Settings → Models → карточка Module API →
«Fetch available models».

## Удаление

Убрать `dsh-moduleapi` из `dsh.profile.bundles` и `dependencies`
в `%USERPROFILE%\.dsh\profiles\desktop\package.json`, затем `npx pnpm@latest install`.

## Roadmap

- v0.2 — собственный адаптер со всеми 26 моделями Module API и пресетом агента по умолчанию.
