import psycopg

passwords = ["postgres", "admin", "123456", "postgres_dev_password", "root", "1234", "masterkey"]
ports = [5432, 5433]

found = False
for port in ports:
    for pwd in passwords:
        try:
            conn = psycopg.connect(f"postgresql://postgres:{pwd}@localhost:{port}/postgres", autocommit=True)
            print(f"SUCESSO! Porta: {port}, Senha: {pwd}")
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pg_database WHERE datname='telesys_erp'")
            if not cur.fetchone():
                cur.execute("CREATE DATABASE telesys_erp")
                print("Banco telesys_erp criado com sucesso!")
            else:
                print("Banco telesys_erp já existe!")
            conn.close()
            found = True
            break
        except Exception as e:
            pass
    if found:
        break

if not found:
    print("Nenhuma das senhas padrão funcionou. Testaremos autenticação SSPI/Trust ou solicitação de senha.")
