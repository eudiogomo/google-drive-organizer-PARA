# 🗂️ Google Drive Organizer — Método P.A.R.A. com Claude Code

Um sistema que usa a inteligência do Claude Code para organizar automaticamente seus arquivos do Google Drive seguindo o **método P.A.R.A.** de Tiago Forte. Diferente dos organizadores tradicionais, este propõe um plano completo para sua aprovação antes de mover qualquer arquivo.

> Adaptado de [tharlesamaro/google-drive-organizer](https://github.com/tharlesamaro/google-drive-organizer)

---

## 🎯 O que é o método P.A.R.A.?

O P.A.R.A. é um sistema de organização criado por Tiago Forte que divide tudo em quatro categorias:

| Categoria | O que é | Sinais |
|-----------|---------|--------|
| **Projects** | Trabalhos com resultado específico e prazo | Modificado nos últimos 90 dias, ligado a uma entrega |
| **Areas** | Responsabilidades contínuas sem fim definido | Editado regularmente, domínios da vida (saúde, finanças...) |
| **Resources** | Material de referência e consulta | Pouco editado, serve como consulta futura |
| **Archives** | Itens inativos das outras categorias | Não modificado há mais de 1 ano |

### 📁 Como fica a estrutura no Drive

```
📁 PARA/
├── 📁 Projects/
│   ├── 📁 Website-Redesign/
│   ├── 📁 Q4-Report/
│   └── 📁 App-Launch/
├── 📁 Areas/
│   ├── 📁 Finance/
│   ├── 📁 Health/
│   └── 📁 Career/
├── 📁 Resources/
│   ├── 📁 Templates/
│   ├── 📁 Research/
│   └── 📁 Courses/
└── 📁 Archives/
    ├── 📁 2023-Projects/
    └── 📁 Old-Work/
```

---

## ✨ Diferenciais deste projeto

- 🧠 **Análise inteligente**: Claude Code analisa metadados e padrões de uso dos arquivos
- 👁️ **Revisão antes de executar**: Claude propõe o plano completo e só executa após sua aprovação
- 🏗️ **Estrutura P.A.R.A.**: Organização baseada em metodologia comprovada de produtividade
- 🛡️ **100% seguro**: Apenas move arquivos, nunca deleta

---

## ⚡ Como começar

### 1. Clone o projeto

```bash
git clone https://github.com/seu-usuario/google-drive-organizer-PARA.git
cd google-drive-organizer-PARA
pip install -r requirements.txt
```

### 2. Configure as credenciais do Google Drive

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto (ou use um existente)
3. Ative a **Google Drive API**
4. Crie credenciais **OAuth 2.0** para aplicação desktop
5. Em **Test users**, adicione o e-mail da sua conta Google
6. Baixe o JSON e renomeie para `credentials.json`
7. Coloque o arquivo na pasta raiz do projeto

### 3. Teste a conexão

```bash
python main.py test
```

Se aparecer `Connection OK — found N files at root level`, está tudo certo.

### 4. Execute

```bash
python main.py
```

Depois, no **Claude Code** (no mesmo diretório), peça:

```
Organize meu Google Drive usando o método P.A.R.A.
```

---

## 🔄 Como funciona o fluxo

```
1. ANALYZE   → Claude varre o Drive inteiro e analisa os arquivos
        ↓
2. PLAN      → Claude cria um plano P.A.R.A. com base nos sinais de cada arquivo
        ↓
3. PREVIEW   → Claude exibe o plano completo para sua revisão:
               📁 Projects/ (12 arquivos)
                  └─ Website-Redesign (8 arquivos)
                  └─ Q4-Report (4 arquivos)
               📁 Areas/ (5 arquivos)
                  └─ Finance (5 arquivos)
               ...
        ↓
4. APPROVE   → Você aprova (ou pede ajustes)
        ↓
5. EXECUTE   → Claude move todos os arquivos para a estrutura P.A.R.A.
```

> **Importante:** O Claude nunca executa sem sua aprovação explícita no passo 4.

---

## 🎮 Comandos úteis no Claude Code

```
# Organização completa
Organize meu Google Drive usando o método P.A.R.A.

# Só analisar sem organizar ainda
Analise meu Drive e me mostre a distribuição dos arquivos por categoria P.A.R.A.

# Testar com uma pasta específica
Analise apenas a pasta "Documentos" e proponha uma organização P.A.R.A.

# Ajustar o plano
Mova todos os arquivos de "Finance" para Projects em vez de Areas
```

---

## 🔧 Funcionalidades técnicas

### Ferramentas expostas ao Claude Code

```python
# Varre o Drive e retorna arquivos com sinais P.A.R.A.
data = get_drive_analysis(recursive=True, folder_id="root")
# Retorna: {"files": [...], "stats": {...}, "files_index": {...}}

# Formata o plano proposto para revisão
report = preview_para_plan(plan, files_index)

# Executa o plano aprovado
result = execute_para_organization(plan)
# Retorna: {"folders_created": N, "files_moved": N, "errors": [...]}
```

### Sinais P.A.R.A. calculados por arquivo

| Sinal | Descrição |
|-------|-----------|
| `days_since_modified` | Dias desde a última edição |
| `activity_level` | `active` / `moderate` / `inactive` |
| `mime_type_category` | Document / Spreadsheet / PDF / Image / ... |
| `file_age_days` | Idade total do arquivo |
| `name_keywords` | Palavras-chave extraídas do nome |
| `suggested_category` | Sugestão automática de categoria P.A.R.A. |

---

## 🛡️ Segurança e privacidade

- 🔒 **Credenciais locais**: `credentials.json` e `token.json` ficam apenas no seu computador
- 🏠 **Dados no Google**: Arquivos permanecem na sua conta Google Drive
- 🚫 **Zero deleção**: O sistema apenas move arquivos
- 👁️ **Revisão obrigatória**: Você aprova antes de qualquer alteração
- ↩️ **Reversível**: Mudanças podem ser desfeitas manualmente no Google Drive

---

## 🔧 Problemas comuns e soluções

### Erro 403: "The user does not have sufficient permissions"

1. No [Google Cloud Console](https://console.cloud.google.com/), vá em **APIs & Services > Credentials**
2. Edite suas credenciais OAuth 2.0
3. Em **Test users**, adicione o e-mail da sua conta Google
4. Salve as alterações
5. Delete o arquivo `token.json` (se existir)
6. Execute `python main.py test` novamente e refaça a autorização

### "credentials.json não encontrado"

- Verifique se o arquivo está na pasta raiz do projeto (não em subpastas)
- O nome deve ser exatamente `credentials.json`

### Claude Code não consegue chamar as funções

- Verifique se `python main.py` ainda está rodando no terminal
- Teste com `python main.py test` antes de usar o Claude Code

### Erro de autenticação após longo tempo sem usar

- Delete o arquivo `token.json`
- Execute `python main.py` novamente para refazer a autenticação

---

## 📚 Sobre o método P.A.R.A.

O P.A.R.A. foi criado por Tiago Forte e é descrito em detalhes no livro [*Building a Second Brain*](https://www.buildingasecondbrain.com/). A ideia central é que qualquer informação pode ser classificada em apenas quatro categorias, tornando a organização simples e consistente ao longo do tempo.

---

**💡 O diferencial:** Este projeto não apenas organiza — ele organiza seguindo um método comprovado, propõe o plano para você revisar, e só executa com sua aprovação.
