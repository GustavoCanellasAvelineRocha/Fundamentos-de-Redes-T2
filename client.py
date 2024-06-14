import socket
import time
import zlib
import random

# Configuração de IP
SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
CLIENT_PORT = 12346
BUFFER_TAMANHO = 1024
PROBABILIDADE_DE_ERRO = 0.1  
TAMANHO_DO_PACOTE = 10
TIMEOUT = 1  
ARQUIVO = '100_bytes.txt'

FIN = b'FIN'

def envia_arquivo(endereco_servidor):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', CLIENT_PORT))
        with open(ARQUIVO, 'rb') as arquivo:
            sequencia = 0
            janela = 1
            slow_start_threshold = 16
            dadosRestransmitir = None

            while True:
                for _ in range(janela):
                    if dadosRestransmitir is None:
                        dados = arquivo.read(TAMANHO_DO_PACOTE)
                        if not dados:
                            break
                        crc = zlib.crc32(dados)
                        pacote = sequencia.to_bytes(4, 'big') + dados + crc.to_bytes(4, 'big')
                    else:
                        pacote = dadosRestransmitir
                        
                    # Calculo de erro
                    if random.random() < PROBABILIDADE_DE_ERRO:
                        error_index = random.randint(0, len(pacote) - 1)
                        pacote = pacote[:error_index] + bytes([pacote[error_index] ^ 0xFF]) + pacote[error_index + 1:]
                        dadosRestransmitir = pacote
                    else:
                        dadosRestransmitir = None

                    sock.sendto(pacote, endereco_servidor)
                    print(f"Enviado pacote {sequencia}")
                    sequencia += 1

                if not dados and dadosRestransmitir is None:
                    break
                    
                sequencia-=janela
                for _ in range(janela):
                    try:
                        sock.settimeout(TIMEOUT)
                        ack, _ = sock.recvfrom(BUFFER_TAMANHO)
                        ack_num = int.from_bytes(ack, 'big')
                        if ack_num == sequencia + 1:
                            sequencia += 1
                            if janela < slow_start_threshold:
                                janela *= 2
                            else:
                                janela += 1
                            dadosRestransmitir = None
                        else:
                            raise socket.timeout
                    except socket.timeout:
                        print(f"Timeout no pacote {sequencia}, reiniciando Slow Start")
                        janela = 1
                        break

            sock.sendto(FIN, endereco_servidor)
            print("FIN enviado")

envia_arquivo((SERVER_IP, SERVER_PORT))
