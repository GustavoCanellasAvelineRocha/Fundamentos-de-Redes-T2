import socket
import zlib

# Configuração de IP

SERVER_IP = '127.0.0.1'
SERVER_PORT = 12345
CLIENT_PORT = 12346
BUFFER_TAMANHO = 1024

FIN = b'FIN'

def recebe_arquivo(client_address):
    print("Servidor iniciado")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((SERVER_IP, SERVER_PORT))
        dados_recebidos = {}
        sequencia_acks_esperada = 0
        
        while True:
            packet, addr = sock.recvfrom(BUFFER_TAMANHO)
            if addr == client_address:
                if packet == FIN:
                    print("EOF marker received")
                    break
                
                seq_num = int.from_bytes(packet[:4], 'big')
                data = packet[4:-4]
                crc = int.from_bytes(packet[-4:], 'big')
                
                if zlib.crc32(data) == crc:
                    if seq_num == sequencia_acks_esperada:
                        dados_recebidos[seq_num] = data
                        sequencia_acks_esperada += 1
                        ack = (seq_num + 1).to_bytes(4, 'big')
                        sock.sendto(ack, client_address)
                        print(f"Recebido pacote {seq_num}, enviado ACK {seq_num + 1}")
                    else:
                        ack = sequencia_acks_esperada.to_bytes(4, 'big')
                        sock.sendto(ack, client_address)
                        print(f"Pacote fora de ordem {seq_num}, reenviado ACK {sequencia_acks_esperada}")
                else:
                    print(f"Erro de CRC no pacote {seq_num}, descartado")
                    
        with open('Arquivo_recebido.txt', 'wb') as f:
            for seq_num in sorted(dados_recebidos.keys()):
                f.write(dados_recebidos[seq_num])
                
        print(f"Arquivo salvo!")

recebe_arquivo((SERVER_IP, CLIENT_PORT))
