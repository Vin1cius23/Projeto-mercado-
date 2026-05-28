# -*- coding: utf-8 -*-
import sqlite3
import unicodedata
import os

def normalize_name(name):
    """Normalize a product name to help detect duplicates robustly."""
    if not name:
        return ""
    # Convert to lowercase, strip leading/trailing spaces
    name = name.strip().lower()
    # Decompose unicode characters to separate letters from accents
    nfd_form = unicodedata.normalize('NFD', name)
    # Reconstruct string without accent characters (Mn category = Nonspacing Mark)
    name_clean = "".join(c for c in nfd_form if unicodedata.category(c) != 'Mn')
    return name_clean

def main():
    db_path = "kiosk.db"
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found in current directory.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Retrieve all existing products
    cursor.execute("SELECT code, name, category, price FROM products")
    existing_rows = cursor.fetchall()
    
    # Map normalized names to codes/categories for quick lookup
    existing_normalized = {}
    for code, name, cat, price in existing_rows:
        norm = normalize_name(name)
        existing_normalized[norm] = (code, name, cat, price)
        print(f"Existing in DB: Code={code}, Name='{name}' (Normalized='{norm}'), Cat='{cat}', Price={price}")

    # List of new products provided by the user
    # Format: (Name, Category, Suggested Price, Description)
    new_products = [
        # Category: Pães
        ("Pão francês", "Pães", 1.50, "Pão francês fresquinho e crocante."),
        ("Pão de leite", "Pães", 2.50, "Pão de leite macio e saboroso."),
        ("Pão integral", "Pães", 4.50, "Pão integral rico em fibras."),
        ("Pão de forma", "Pães", 7.50, "Pão de forma tradicional fatiado."),
        ("Pão australiano", "Pães", 6.00, "Pão australiano escuro e levemente adocicado."),
        ("Pão de queijo", "Pães", 4.50, "Pão de queijo quentinho e crocante."),
        ("Baguete", "Pães", 5.00, "Baguete tradicional crocante."),
        ("Bisnaga", "Pães", 3.00, "Bisnaga macia, ideal para lanches."),
        ("Croissant", "Pães", 8.00, "Croissant folhado amanteigado."),
        
        # Category: Bolos e Tortas
        ("Bolo de chocolate", "Bolos e Tortas", 15.00, "Delicioso bolo de chocolate com cobertura."),
        ("Bolo de cenoura", "Bolos e Tortas", 12.00, "Bolo de cenoura com calda de chocolate."),
        ("Bolo de fubá", "Bolos e Tortas", 10.00, "Bolo de fubá caseiro tradicional."),
        ("Bolo de milho", "Bolos e Tortas", 10.00, "Bolo de milho cremoso irresistível."),
        ("Torta de frango", "Bolos e Tortas", 8.50, "Torta salgada de frango desfiado temperado."),
        ("Torta de palmito", "Bolos e Tortas", 9.00, "Torta salgada com recheio cremoso de palmito."),
        ("Cheesecake", "Bolos e Tortas", 14.00, "Cheesecake clássica com calda de frutas vermelhas."),
        ("Rocambole", "Bolos e Tortas", 12.00, "Rocambole doce recheado."),
        
        # Category: Salgados
        ("Coxinha", "Salgados", 6.50, "Coxinha de frango frita na hora."),
        ("Esfiha", "Salgados", 6.00, "Esfiha assada de carne ou queijo."),
        ("Empada", "Salgados", 5.50, "Empada de frango ou palmito massa podre."),
        ("Pastel", "Salgados", 7.00, "Pastel frito super crocante."),
        ("Quibe", "Salgados", 6.00, "Quibe frito tradicional temperado com hortelã."),
        ("Enroladinho de salsicha", "Salgados", 5.50, "Enroladinho de salsicha assado e macio."),
        ("Pão de batata", "Salgados", 6.50, "Pão de batata macio com requeijão."),
        ("Risole", "Salgados", 6.00, "Risole frito com recheio cremoso."),
        
        # Category: Doces
        ("Brigadeiro", "Doces", 4.00, "Brigadeiro de chocolate gourmet com granulado."),
        ("Beijinho", "Doces", 4.00, "Doce de coco tradicional com cravo."),
        ("Sonho", "Doces", 6.00, "Sonho tradicional recheado com creme de confeiteiro."),
        ("Carolinas", "Doces", 8.00, "Carolinas recheadas com doce de leite e cobertura de chocolate."),
        ("Bombom", "Doces", 3.50, "Bombom artesanal de sabores variados."),
        ("Pudim", "Doces", 7.50, "Fatia de pudim de leite condensado super cremoso."),
        ("Quindim", "Doces", 6.50, "Quindim tradicional brilhante e saboroso."),
        ("Cookie", "Doces", 5.00, "Cookie com gotas de chocolate crocante por fora e macio por dentro."),
        
        # Category: Frios e Laticínios
        ("Presunto", "Frios e Laticínios", 6.00, "Fatias finas de presunto cozido (100g)."),
        ("Queijo muçarela", "Frios e Laticínios", 7.00, "Fatias de queijo muçarela fresco e derretível (100g)."),
        ("Queijo prato", "Frios e Laticínios", 7.50, "Fatias de queijo prato fatiado (100g)."),
        ("Requeijão", "Frios e Laticínios", 8.50, "Copo de requeijão cremoso tradicional (200g)."),
        ("Manteiga", "Frios e Laticínios", 9.00, "Manteiga com sal de primeira qualidade (200g)."),
        ("Cream cheese", "Frios e Laticínios", 10.00, "Cream cheese cremoso e suave (150g)."),
        ("Iogurte", "Frios e Laticínios", 5.00, "Iogurte natural ou de frutas refrescante."),
        
        # Category: Bebidas
        ("Café", "Bebidas", 3.00, "Café passado na hora quente e aromático."),
        ("Café com leite", "Bebidas", 5.00, "Café com leite quentinho e equilibrado."),
        ("Cappuccino", "Bebidas", 8.00, "Cappuccino cremoso com chocolate e canela."),
        ("Chocolate quente", "Bebidas", 8.00, "Chocolate quente cremoso e aconchegante."),
        ("Suco natural", "Bebidas", 7.50, "Suco natural feito com frutas frescas da época."),
        ("Refrigerante", "Bebidas", 7.00, "Refrigerante em lata geladinho."),
        ("Água mineral", "Bebidas", 3.00, "Garrafa de água mineral pura e fresca."),
        ("Energético", "Bebidas", 10.00, "Lata de energético gelado para dar um up."),
        
        # Category: Biscoitos e Snacks
        ("Rosquinha", "Biscoitos e Snacks", 5.00, "Pacote de rosquinhas crocantes doces."),
        ("Torrada", "Biscoitos e Snacks", 4.50, "Torradas crocantes tradicionais."),
        ("Biscoito amanteigado", "Biscoitos e Snacks", 6.00, "Biscoito amanteigado derrete na boca."),
        ("Bolacha recheada", "Biscoitos e Snacks", 4.00, "Pacote de bolacha recheada sabor chocolate ou morango."),
        ("Salgadinho", "Biscoitos e Snacks", 5.00, "Pacote de salgadinho de milho ou batata."),
        ("Amendoim", "Biscoitos e Snacks", 4.00, "Pacote de amendoim torrado e salgado."),
    ]

    current_code = 300
    inserted_count = 0
    skipped_count = 0

    print("\n--- INICIANDO PROCESSAMENTO DE IMPORTAÇÃO ---")
    for name, category, price, desc in new_products:
        norm_name = normalize_name(name)
        
        # Special check: If name is 'cafe', does 'cafe expresso' count as a duplicate? Yes, or if 'cafe' is a substring of anything, or matches exactly.
        # Let's check for exact normalized matches, or direct overlaps.
        # In typical setups, "cafe" will match "cafe expresso" as a duplicate if we do fuzzy matching, or we can do exact normalized matching.
        # Let's do exact normalized matching first, but also handle special cases like "cafe" -> "cafe expresso".
        is_duplicate = False
        duplicate_reason = ""
        
        if norm_name in existing_normalized:
            is_duplicate = True
            duplicate_reason = f"Existe exatamente com o código {existing_normalized[norm_name][0]}"
        elif norm_name == "cafe" and "cafe expresso" in existing_normalized:
            is_duplicate = True
            duplicate_reason = "Café Expresso já cadastrado no sistema."
        
        if is_duplicate:
            print(f"[-] Ignorado (Duplicado): '{name}' - Categoria: {category} ({duplicate_reason})")
            skipped_count += 1
            continue
        
        # If not duplicate, insert
        # Auto-increment code until we find one that's not used
        while True:
            cursor.execute("SELECT 1 FROM products WHERE code = ?", (str(current_code),))
            if not cursor.fetchone():
                break
            current_code += 1
        
        code_str = str(current_code)
        image_default = "1zYZMU.png"
        
        cursor.execute(
            "INSERT INTO products (code, name, category, price, image, description) VALUES (?, ?, ?, ?, ?, ?)",
            (code_str, name, category, price, image_default, desc)
        )
        print(f"[+] INSERIDO: Cód={code_str} | '{name}' | R$ {price:.2f} | Categoria: {category}")
        
        # Add to local tracking so we don't insert duplicates within the list itself
        existing_normalized[norm_name] = (code_str, name, category, price)
        inserted_count += 1
        current_code += 1

    conn.commit()
    conn.close()
    
    print("\n--- RESUMO DA IMPORTAÇÃO ---")
    print(f"Total de produtos inseridos com sucesso: {inserted_count}")
    print(f"Total de produtos ignorados (duplicados): {skipped_count}")

if __name__ == "__main__":
    main()
