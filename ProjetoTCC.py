import pytsk3
import os

def abrir_imagem(caminho_imagem, offset=0):
    """Abre uma imagem para análise forense"""
    try:
        img = pytsk3.Img_Info(caminho_imagem)
        fs = pytsk3.FS_Info(img, offset * 512)  # offset em setores convertido para bytes
        return fs
    except Exception as e:
        print(f"Erro ao abrir imagem: {e}")
        return None

def detectar_offset(caminho_imagem):
    try:
        img = pytsk3.Img_Info(caminho_imagem)
        volume = pytsk3.Volume_Info(img)

        for particao in volume:
            if particao.len > 2048:
                print(f"Particao encontrada no offset: {particao.start} setores")
                return particao.start
        print("Nenhuma particao válida encontrada")
        return None
    except Exception as e:
        print(f"Erro ao detectar offset: {e}")
        return None

def listar_arquivos(fs, diretorio='/', lista=None):
    #Percorre a imagem e retorna lista de arquivos
    if lista is None:
        lista = []
    dir_handle = fs.open_dir(diretorio)
    for entry in dir_handle:
        if not hasattr(entry, "info") or not hasattr(entry.info, "name"):
            continue
        nome = entry.info.name.name.decode(errors='ignore')
        if nome in [".",".."]:
            continue
        caminho_completo = os.path.join(diretorio, nome)

        #Recursão se for diretório
        if entry.info.name.type == pytsk3.TSK_FS_NAME_TYPE_DIR:
            try:
                listar_arquivos(fs, caminho_completo, lista)
            except Exception:
                pass
            continue

        #Se o arquivo for deletado, adiciona na lista
        if (entry.info.name.type == pytsk3.TSK_FS_NAME_TYPE_REG and
                entry.info.meta and
                entry.info.meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC):
            lista.append({
                "nome": nome,
                "caminho": caminho_completo,
                "tamanho": entry.info.meta.size,
                "inode": entry.info.meta.addr
            })
    return lista

def recuperar_arquivos(fs, arquivo, pasta_saida):
    #Recupera um único arquivo através do seu inode
    nome = arquivo["nome"]
    inode = arquivo["inode"]
    tamanho = arquivo["tamanho"]

    if nome[0] in ("_", "?"):
        nome = "REC_" + nome[1:]

    try:
        file_obj = fs.open_meta(inode)
        caminho_saida = os.path.join(pasta_saida, nome)

        if os.path.exists(caminho_saida):
            base, ext = os.path.splitext(nome)
            contador = 1
            while os.path.exists(caminho_saida):
                nome = f"{base}_{contador}{ext}"
                caminho_saida = os.path.join(pasta_saida, nome)
                contador += 1

        with open(caminho_saida, 'wb') as out:
            CHUNK = 1024*1024
            lido = 0
            while lido < tamanho:
                restante = min(CHUNK, tamanho - lido)
                data = file_obj.read_random(lido, restante)
                if not data:
                    break
                out.write(data)
                lido += len(data)
        print(f"Recuperado: {caminho_saida}")
    except Exception as e:
        print(f"Erro ao recuperar arquivo {nome}: {e}")


if __name__ == "__main__":
    print("~~~~ FERRAMENTA DE RECUPERAÇÃO DE ARQUIVOS DELETADOS ~~~~\n")

    #Pedido ao usuário no terminal
    caminho_imagem = input("Caminho da imagem: ").strip('"')
    caminho_saida = input("Caminho da saida: ").strip('"')

    print("\nDetectando offset...")
    offset = detectar_offset(caminho_imagem)

    if offset is None:
        print("Não foi possível detectar o offset")
        offset = int(input("Digite o offset manualmente: "))
    else:
        print(f"Offset: {offset}")

    fs = abrir_imagem(caminho_imagem, offset)

    if not fs:
        print("Falha ao abrir imagem. Verifique o caminho e o offset.")
    else:
        print("Varredura em andamento...\n")
        arquivos = listar_arquivos(fs)
        if not arquivos:
            print("Nenhum arquivo encontrado.")
        else:
            print(f"{'#':<5} {'Nome':<30} {'Tamanho':<15} {'Inode':<10} Caminho")
            print("~" * 80)
            for i, arq in enumerate(arquivos):
                print(f"{i:<5} {arq['nome']:<30} {arq['tamanho']:<15} {arq['inode']:<10} {arq['caminho']}")
            print("\nDigite os número dos arquivos que deseja recuperar:")
            print("Separe por vírgula para múltiplos (ex: 0,2,5) ou 'todos' para recuperar tudo.\n")

            escolha = input("Escolha: ").strip().lower()
            os.makedirs(caminho_saida, exist_ok=True)

            if escolha == "todos":
                for arq in arquivos:
                    recuperar_arquivos(fs, arq, caminho_saida)
            else:
                try:
                    indices = [int(x.strip()) for x in escolha.split(",")]
                    for i in indices:
                        if 0 <= i < len(arquivos):
                            recuperar_arquivos(fs, arquivos[i], caminho_saida)
                        else:
                            print(f"Indice {i} inválido, ignorado.")
                except ValueError:
                    print("Entrada inválida. Use números separados por vírgula ou 'todos'.")