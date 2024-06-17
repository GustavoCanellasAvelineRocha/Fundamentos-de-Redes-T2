import socket
import time
import zlib
import random

# Configuração de IP
SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
CLIENT_PORT = 12346
BUFFER_TAMANHO = 1024
LIMITE_SLOW_START = 16
PROBABILIDADE_DE_ERRO = 0.1
TAMANHO_DO_PACOTE = 10
TIMEOUT = 1  
ARQUIVO = '500_bytes.txt'

ACK = b'ACK'
FIN = b'FIN'

def envia_arquivo(endereco_servidor):
    print("Cliente iniciado!")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('', CLIENT_PORT))
        print("Estabelecendo Conexão!")
        sock.sendto(ACK, endereco_servidor)
        packet, addr = sock.recvfrom(BUFFER_TAMANHO)
        
        if packet == ACK:
            print(f"Conexão estabelecida com o servidor {addr}, iniciando envio de Pacotes...")
            
            with open(ARQUIVO, 'rb') as arquivo:
                sequenciaDados = 0
                ultimoPacote = -1
                arrayDados = {}
                arrayACKs = {}
                sequencia = 0
                janela = 1
                dadosRestransmitir = False

                while True:
                    print(f"Enviando Arquivos, tamanho da janela atual {janela}")
                    for _ in range(janela):
                        dados = arquivo.read(TAMANHO_DO_PACOTE)
                        if not dados:
                            ultimoPacote = sequenciaDados
                            break
                        arrayDados[sequenciaDados] = dados
                        crc = zlib.crc32(dados)
                        pacote = sequenciaDados.to_bytes(4, 'big') + dados + crc.to_bytes(4, 'big')
                            
                        # Calculo de erro
                        if random.random() < PROBABILIDADE_DE_ERRO:
                            print(f"Pacote com erro {sequenciaDados}")
                            error_index = random.randint(4, len(pacote) - 1) 
                            pacote = pacote[:error_index] + bytes([pacote[error_index] ^ 0xFF]) + pacote[error_index + 1:]

                        sock.sendto(pacote, endereco_servidor)
                        print(f"Enviado pacote {sequenciaDados}")
                        sequenciaDados += 1
                    
                    i = 0
                    while i < janela:
                        try:
                            if sequencia == ultimoPacote:
                                break
                            sock.settimeout(TIMEOUT)
                            ack, _ = sock.recvfrom(BUFFER_TAMANHO)
                            ack_num = int.from_bytes(ack, 'big')
                            print(f'ACK recebido {ack_num}')
                            if ack_num == sequencia + 1:
                                arrayACKs[ack_num - 1] = True
                                sequencia += 1
                                i += 1
                                j = sequencia
                                while j < len(arrayACKs):
                                    if arrayACKs[j] == True:
                                        j += 1
                                        sequencia += 1
                                    else:
                                        break
                            elif ack_num > sequencia + 1:
                                arrayACKs[ack_num - 1] = True
                                i += 1
                            else:
                                raise socket.timeout
                            sock.settimeout(TIMEOUT)
                        except socket.timeout:
                            dadosRestransmitir = True
                            print(f"Timeout no pacote {sequencia}")
                            
                            dados = arrayDados.get(sequencia)
                            crc = zlib.crc32(dados)
                            pacote = sequencia.to_bytes(4, 'big') + dados + crc.to_bytes(4, 'big')
                                
                            # Calculo de erro
                            if random.random() < PROBABILIDADE_DE_ERRO:
                                error_index = random.randint(4, len(pacote) - 1) 
                                pacote = pacote[:error_index] + bytes([pacote[error_index] ^ 0xFF]) + pacote[error_index + 1:]

                            sock.sendto(pacote, endereco_servidor)
                            print(f"Reenviado pacote {sequencia}")
                            
                    if sequencia == ultimoPacote:
                        break
                    if dadosRestransmitir:
                        janela = 1
                        dadosRestransmitir = False
                        print(f"Houve reetransmissao, reiniciando Slow Start.")
                    else:
                        if janela < LIMITE_SLOW_START:
                            janela *= 2
                        else:
                            janela += 1

                sock.sendto(FIN, endereco_servidor)
                print("FIN enviado")
                while True:
                    try:
                        sock.settimeout(TIMEOUT)
                        packet, addr = sock.recvfrom(BUFFER_TAMANHO)
                        if packet == ACK:
                            print(f"ACK recebido, conexão encerrada.")
                            break
                        else:
                            print(f"Erro na desconexão, pacote inesperado recebido: {packet}")
                    except socket.timeout:
                        print(f"Timeout aguardando ACK, reenviando FIN...")
                        sock.sendto(FIN, endereco_servidor)
        else:
            print(f"Erro na Conexão")

envia_arquivo((SERVER_IP, SERVER_PORT))
