# Equipamentos

Os equipamentos em `equipment.py` usam preços em peças de ouro e pesos em
libras. Os exemplos incluídos são espada longa, adaga, arco curto, armadura
de couro, camisa de malha, cota de malha e poção de cura. `Weapon` e `Armor`
também permitem criar outros equipamentos; `magic_bonus` acrescenta bônus
mágico à CA ou às jogadas de ataque e dano.

```python
from character import Character
from equipment import HealingPotion, chain_shirt, longsword

hero = Character("Hero")
sword = longsword()
armor = chain_shirt()
hero.add_item(sword)
hero.add_item(armor)
hero.equip(sword)
hero.equip(armor)
print(hero.get_armor_class())

hero.add_item(HealingPotion())
print(hero.use_item("Potion of Healing"))
# Para administrar a outro personagem: hero.use_item("Potion of Healing", ally)
```

Cada objeto representa uma unidade; crie objetos separados para itens
repetidos. Equipar exige que o item esteja no inventário; remover o item
equipado também o desequipa. Use `unequip_weapon()` e `unequip_armor()` para
desequipar sem remover. Uma poção usada é retirada do inventário e não pode
ser reutilizada. Para outros efeitos, `Potion` recebe uma função que aplica
o efeito ao alvo e retorna uma mensagem.

A CA usa a fórmula da armadura leve, média ou pesada, inclusive o limite de
Destreza das armaduras médias. Armas à distância usam Destreza e armas com
Finesse usam o maior modificador de Força ou Destreza. O sistema existente
de ataque e personagens ainda usa regras D20 anteriores: não foi convertido
integralmente para 5.2.1. Proficiências, propriedades adicionais
das armas (incluindo duas mãos e Versatile), alcance, ações e restrições
de armadura não são aplicados; o chamador deve controlar ações e distância
ao administrar poções.

Na criação, o personagem recebe 1.000 peças de ouro e pode comprar equipamentos
na tela seguinte. Clique nos espaços para ver as opções; a mochila permite
comprar poções e pacotes de 10 rações repetidamente. Arma, peitoral e escudo
são equipados automaticamente. O escudo especial concede +3 à CA. Voltar
restaura o ouro e desfaz todas as compras; Prosseguir mantém os itens.
Os preços da loja são específicos desta etapa, incluindo 50 po pela espada.

# Taverna

Após equipar o herói, clique em Theron, Aveline ou no quadro de avisos para
interagir. No quadro, aceite missões e examine a ficha dos possíveis
companheiros antes de recrutá-los. A ficha pode ser rolada com a roda do
mouse ou com as setas. O carisma do
herói determina o limite de recrutas: zero até 10, um por ponto acima de 10,
até o máximo de cinco; nenhum recruta pode ter carisma maior que o do herói.
O nível do recruta também deve ser igual ou inferior ao do herói. O grupo
inclui o herói e tem no máximo seis integrantes.

Após aceitar uma missão, aparece o botão para sair. Missões, diálogos e
recrutas são provisórios: sair leva a uma tela temporária, de onde é possível
voltar à taverna. As aventuras ainda não estão implementadas.

# Salvamento

Durante o jogo, pressione Esc para salvar, carregar ou voltar à tela principal.
Há um único arquivo, `savegame.json`, na pasta do projeto; salvar novamente
pede confirmação antes de substituí-lo. Carregar avisa que o progresso não
salvo será perdido. Ao voltar à tela principal, escolha salvar, não salvar ou
cancelar; também é possível continuar a sessão em memória ou carregar o
arquivo pelo menu inicial.

O salvamento preserva o grupo, atributos, retratos, inventários, magias,
equipamentos, missões aceitas e local atual. Poções de efeito personalizado e
outros tipos de itens ou magias não cadastrados não são serializados: nesse
caso o jogo informa o erro sem substituir o arquivo existente.

Dados e fórmulas de equipamentos baseados no
[System Reference Document 5.2.1](https://www.dndbeyond.com/srd), publicado
pela Wizards of the Coast sob [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
