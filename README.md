# Sistema de Monitoramento de Câmeras com FastAPI

Este projeto implementa um sistema de monitoramento de câmeras utilizando FastAPI para download de vídeos, extração de frames e detecção de veículos. O sistema é capaz de baixar vídeos periodicamente de várias câmeras, pausar e retomar os downloads, extrair frames dos vídeos e fornecer informações sobre as câmeras e os frames extraídos via endpoints API.

## Funcionalidades

- Download periódico de vídeos de várias câmeras.
- Capacidade de pausar e retomar o download dos vídeos.
- Extração de frames dos vídeos mais recentes com base em um timestamp especificado.
- Endpoints API para listar câmeras, pausar/resumir downloads e obter informações dos frames extraídos.

## Tecnologias Utilizadas

- [FastAPI](https://fastapi.tiangolo.com/)
- [aiohttp](https://docs.aiohttp.org/en/stable/)
- [OpenCV](https://opencv.org/)
- [Uvicorn](https://www.uvicorn.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)

## Instalação

1. Clone o repositório:

   ```sh
   git clone https://github.com/seu_usuario/seu_repositorio.git
   cd seu_repositorio
   
2. Crie um ambiente virtual e ative-o:

  python -m venv venv
  source venv/bin/activate  # No Windows, use `venv\Scripts\activate`

3. Instale as dependências:

  pip install -r requirements.txt

4. Execute o servidor FastAPI:

  uvicorn main:app --reload
