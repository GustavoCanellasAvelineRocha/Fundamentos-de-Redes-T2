import socket
import zlib

# Configuração de IP

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
CLIENT_PORT = 12346
BUFFER_TAMANHO = 1024

ACK = b'ACK'
FIN = b'FIN'

def recebe_arquivo(endereco_cliente):
    print("Servidor iniciado!")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock: 
        sock.bind((SERVER_IP, SERVER_PORT))
        print(f"Aguardando Conexão...")
        packet, addr = sock.recvfrom(BUFFER_TAMANHO)
       
        if(packet == ACK ):
            print(f"Conexão estabelecida com o cliente {addr}, enviando ACK")
            sock.sendto(ACK, endereco_cliente)
            dados_recebidos = {}
            arrayACKs = {}
            sequencia_acks_esperada = 0
            
            while True:
                packet, addr = sock.recvfrom(BUFFER_TAMANHO)
                if addr == endereco_cliente:
                    if packet == FIN:
                        print("FIN recebido, transmitindo ACK...")
                        sock.sendto(ACK, endereco_cliente)
                        break
                    
                    numero_sequencia_pacote = int.from_bytes(packet[:4], 'big')
                    data = packet[4:-4]
                    crc = int.from_bytes(packet[-4:], 'big')
                    
                    if zlib.crc32(data) == crc:
                        if numero_sequencia_pacote == sequencia_acks_esperada:
                            dados_recebidos[numero_sequencia_pacote] = data
                            sequencia_acks_esperada += 1
                            ack = (numero_sequencia_pacote + 1).to_bytes(4, 'big')
                            sock.sendto(ack, endereco_cliente)
                            print(f"Recebido pacote {numero_sequencia_pacote}, enviado ACK {numero_sequencia_pacote + 1}")
                            
                            while sequencia_acks_esperada < len(arrayACKs):
                                    if arrayACKs[i] == True:
                                        sequencia_acks_esperada+=1
                                        ack = (numero_sequencia_pacote + 1).to_bytes(4, 'big')
                                        sock.sendto(ack, endereco_cliente)
                                        print(f"Recebido pacote {numero_sequencia_pacote}, enviado ACK {numero_sequencia_pacote + 1}")
                                    else:
                                        break
                        else:
                            dados_recebidos[numero_sequencia_pacote] = data
                            arrayACKs[numero_sequencia_pacote] = True
                            print(f"Pacote fora de ordem {numero_sequencia_pacote}, salvando no array de ACKs {sequencia_acks_esperada}")
                    else:
                        print(f"Erro de CRC no pacote {numero_sequencia_pacote}, descartado")
                        
            with open('Arquivo_recebido.txt', 'wb') as arquivo:
                i=0
                while i in dados_recebidos:
                    arquivo.write(dados_recebidos[i])
                    i += 1
            print(f"Conexão encerrada.")    
            print(f"Arquivo salvo!")

recebe_arquivo((SERVER_IP, CLIENT_PORT))
