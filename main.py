# ===================== Chat Inteligente ===================== #

from core.autotokenizer import autotokenize
from rich.console import Console
from rich.table import Table
from rich import box

# ===================== Classe Principal ===================== #
class Chat:
    EXIT = {"sair", "exit", "quit"}  # Comandos para encerrar o chat

    def __init__(self):
        self.console = Console()

    def log_tokenized(self, result):
        table = Table(title="TokenizedCommand", box=box.SIMPLE)
        table.add_column("Campo", style="bold cyan")
        table.add_column("Valor", style="white")
        table.add_row("original_text", str(result.original_text))
        table.add_row("normalized_text", str(result.normalized_text))
        table.add_row("tokens", str(result.tokens))
        table.add_row("classified_tokens", str(result.classified_tokens))
        table.add_row("action", str(result.action))
        table.add_row("target", str(result.target))
        table.add_row("context", str(result.context))
        table.add_row("confidence", f"{result.confidence:.2f}")
        table.add_row("metadata", str(result.metadata))
        self.console.print(table)

    def run(self):
        while True:
            txt = input("Você: ")

            # Verifica se a mensagem é um comando de saída
            if txt.lower() in self.EXIT:
                print("Encerrando o chat. Até logo!")
                break

            # Processa a entrada do usuário usando o AutoTokenizer
            result = autotokenize(txt)
            self.log_tokenized(result)

# ===================== Execução ===================== #
if __name__ == "__main__":
    Chat().run()

# ===================== Classe Principal ===================== #
class Chat:
    EXIT = {"sair", "exit", "quit"}  # Comandos para encerrar o chat

    def run(self):
        while True:
            txt = input("Você: ")

            # Verifica se a mensagem é um comando de saída
            if txt.lower() in self.EXIT:
                print("Encerrando o chat. Até logo!")
                break

            # Processa a entrada do usuário usando o AutoTokenizer
            result = autotokenize(txt)
            print(f"Bot: {result}")

# ===================== Execução ===================== #
if __name__ == "__main__":
    Chat().run()
