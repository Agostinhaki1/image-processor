# CLAUDE.md

Este arquivo fornece orientações para o Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

## Visão geral

Este é um microserviço Flask em um único arquivo que recebe uma imagem base (normalmente uma imagem gerada por IA, ex.: DALL-E) e sobrepõe texto/elementos gráficos para produzir slides de carrossel do Instagram. Foi projetado para ser chamado por uma automação externa (ex.: um fluxo n8n/Make) que fornece URLs de imagem e uma especificação de layout em JSON, retornando um PNG renderizado.

Toda a lógica da aplicação está em `image_processor.py` — não há estrutura de pacotes, scaffolding de framework nem suíte de testes.

## Rodando localmente

```bash
pip install -r requirements.txt
python image_processor.py        # roda o servidor de dev do Flask em 0.0.0.0:5000
```

Em produção roda via gunicorn (como usado no Dockerfile):

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 image_processor:app
```

## Docker

```bash
docker build -t image-processor .
docker run -p 5000:5000 image-processor
```

O Dockerfile baixa os arquivos de fonte (Montserrat, Inter) do GitHub durante o build, em `/app/fonts`. Se os downloads falharem, o build cai num fallback silencioso (`fallback.txt`) e o `get_font()` em runtime recorre a `ImageFont.load_default()` — vale lembrar disso ao depurar renderização de texto que parece errada (fonte errada ≠ erro/crash).

Não há suíte de testes, linter ou configuração de CI neste repositório. Também não existe `docker-compose.yml`, apesar do README fazer referência a um.

## Arquitetura

Tudo está em `image_processor.py`. Estrutura importante:

- **Diretórios** (criados no momento do import): `./fonts`, `./assets`, `./output`, `./temp`. `./assets/logo.png` é o logo da marca esperado para a marca d'água; `./output` é onde os slides gerados são salvos e servidos.
- **Resolução de fontes** (`get_font`): um mapa pequeno e fixo (`Montserrat` → Montserrat-Bold, qualquer outra coisa → Inter-Regular) — adicionar uma fonte nova exige editar o dict `FONTS` e o `fonte_map` juntos.
- **Quebra de texto** (`draw_text_with_wrap`): quebra de linha manual usando `draw.textbbox` para medir largura; usada nos blocos de subtítulo/descrição.

### Contrato de request/response

- `POST /process-slide` é o endpoint principal. Espera um corpo JSON aproximadamente assim:
  - `id` — usado para nomear o arquivo de saída (`{id}_final.png`)
  - `imagem_dalle_path` ou `dalle_image_url` — a imagem de origem, podendo ser uma URL HTTP(S) (baixada via `requests`) ou um caminho local
  - `camada_texto` — a camada de texto/overlay, podendo conter (na ordem de desenho): `overlay` (retângulo preto semi-transparente para legibilidade), `titulo` (suporta `\n` ou `quebra_linha` para quebras manuais), `elementos_graficos` (lista de `linha_decorativa` ou `badge`), `subtitulo`, `descricao` (ambos com quebra automática), `bullet_points` (lista de linhas ícone+texto, coloridas em `#0066FF` se `destaque` for true, senão `#666666`)
  - `camada_marca` — a camada de marca: `logo` (redimensionado/colado a partir de `assets/logo.png`, posicionado no canto inferior esquerdo a menos que `posicao` contenha `"right"`) e `handle` (texto @handle, alinhado à direita se `posicao` contiver `"right"`)
  - Os campos/valores misturam chaves em português (`titulo`, `cor`, `tamanho`, `posicao`) com valores em string com sufixo de pixel (ex.: `"32px"`, `"#0066FF"`), tratados via `.replace('px', '')` / `hex_to_rgb`. Mantenha essa convenção de parsing ao estender o schema — não há validação de schema JSON, então entradas malformadas geralmente resultam em um 500 com traceback completo na resposta.
- A ordem de processamento importa: overlay → titulo → elementos_graficos → subtitulo → descricao → bullet_points → logo → handle. Desenhos posteriores sobrepõem os anteriores.
- A resposta inclui `download_url: /download/<filename>`; `GET /download/<filename>` serve o arquivo diretamente de `OUTPUT_DIR` sem sanitização do nome além de `os.path.exists` — cuidado com path traversal se mexer nesse endpoint.
- `GET /` e `GET /health` são endpoints simples de status/informação.

### Padrão de tratamento de erros

`process_slide` envolve todo o pipeline em um único try/except e retorna `{status: 'erro', erro, stack, timestamp}` com HTTP 500 em qualquer falha, incluindo o traceback completo do Python. Isso é intencional para facilitar a depuração pelo chamador externo, mas significa que os erros não são diferenciados por tipo (ex.: entrada inválida vs. falha de download vs. falha de renderização) — se precisar de respostas de erro mais granulares, adicione checagens explícitas (ex.: `dalle_url` ausente) antes do except genérico.

### Convenção de idioma

Identificadores de código, mensagens de log e o schema do payload JSON (`camada_texto`, `titulo`, `cor`, etc.) estão em português; mantenha novos campos/mensagens de log consistentes com isso em vez de misturar inglês.
