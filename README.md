# Ferramenta de Recuperação de Arquivos Deletados

Ferramenta desenvolvida em Python para recuperação de arquivos deletados
em imagens de disco no formato `.dd`, utilizando a biblioteca PyTSK3.

Desenvolvida como parte do TCC do curso de Engenharia de computação — PUC Goiás.

## Requisitos
- Python 3.14
- pytsk3
- The Sleuth Kit (para geração de imagens .dd)

## Como usar
1. Gere uma imagem .dd do dispositivo desejado
2. Execute o script: `ProjetoTCC.py`
3. Informe o caminho da imagem e da pasta de saída
4. Selecione os arquivos a recuperar

## Limitações
- Opera apenas sobre imagens .dd, não sobre discos físicos diretamente
- Arquivos cujos setores foram sobrescritos não podem ser recuperados
- Detecção de extensão automática não implementada nesta versão
