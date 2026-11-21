# Sistema de Spells em Combate

## Visão Geral

Implementei um sistema completo de lançamento de spells durante o combate táti co. Os usuários de magia agora podem preparar e lançar seus spells preparados com suporte a:

- ✅ Verificação de disponibilidade de slots de spell
- ✅ Validação de alcance
- ✅ Visualização de spells disponíveis
- ✅ Seleção de alvo com feedback visual
- ✅ Consumo de slots quando o spell é lançado
- ✅ Integração com sistema de dano/efeito existente

## Como Usar

### Durante o Turno do Jogador

1. **Abrir menu de Spells**: 
   - Pressione **S** ou clique no botão "Magia (S)" no lado direito da tela
   - O botão só aparece se o personagem tiver spells preparados
   - O botão fica desativado se a ação de combate já foi usada

2. **Selecionar um Spell**:
   - Uma lista de spells preparados aparecerá no lado esquerdo
   - Cada spell mostra seu nome e quantos slots disponíveis (ou "cantrip")
   - Clique no spell desejado

3. **Escolher um Alvo**:
   - Depois de selecionar o spell, clique em um inimigo no grid
   - O sistema verifica automaticamente o alcance do spell
   - Se o alvo estiver fora do alcance, recebe uma mensagem de erro
   - O spell é lançado e o alvo recebe os efeitos (dano, etc)

4. **Cancelar Seleção**:
   - Pressione **ESC** para cancelar a seleção de spell
   - Pressione **ESC** novamente se tiver selecionado um spell e quiser voltar à lista

### Comportamento de Spells

#### Verificação de Slots
- Cantrips (nível 0) são infinitos
- Spells de nível 1+ consomem slots
- Apenas spells preparados podem ser lançados
- O sistema usa `character.can_cast_spell()` para validar

#### Alcance
- Convertido de pés para tiles (1 tile = 5 pés)
- Se `range_ft = 120`, o alcance é 24 tiles
- O sistema calcula distância Manhattan (movimento em 4 direções)

#### Efeito do Spell
- O sistema chama `character.cast_spell(spell, target)`
- O spell é executado e aplica seus efeitos (dano, buff, etc)
- Consumo de slots é automático

## Exemplos de Spells Disponíveis

### Magic Missile (Míssil Mágico)
- **Nível**: 1
- **Alcance**: 120 ft (24 tiles)
- **Efeito**: 3d4+3 dano de força, sempre acerta
- **Slots**: Consumir 1 slot de nível 1

### Shield (Escudo)
- **Nível**: 1
- **Alcance**: 0 ft (self)
- **Efeito**: +4 bônus de CA por 1 rodada
- **Slots**: Consumir 1 slot de nível 1

### Fire Bolt (Parafuso de Fogo) - Cantrip
- **Nível**: 0
- **Alcance**: 120 ft
- **Efeito**: 1d10 dano de fogo
- **Slots**: Infinito (cantrip)

### Fireball (Bola de Fogo)
- **Nível**: 3
- **Alcance**: 150 ft (30 tiles)
- **Efeito**: 8d6 dano de fogo em área
- **Slots**: Consumir 1 slot de nível 3

## Implementação Técnica

### Arquivos Modificados

1. **combat.py**
   - `_get_castable_spells()`: Retorna lista de spells que podem ser lançados
   - `_start_spell_selection()`: Inicializa o modo de seleção de spell
   - `_cast_spell_on_target()`: Lança o spell em um alvo com validações
   - `_cancel_spell_selection()`: Cancela seleção de spell
   - `handle_event()`: Estendido para suportar eventos de spell
   - `draw()`: Adiciona UI para seleção de spells

2. **character.py**
   - `__init__()`: Agora chama `_update_derived_stats()` para inicializar spell_slots

### Constantes Adicionadas

```python
SPELL_PANEL_WIDTH = 220  # Largura do painel de seleção de spells
```

### Estados do Combat

- `spell_selection_active`: Boolean indicando se está em modo de seleção
- `selected_spell`: Spell atualmente selecionado (None ou Spell object)
- `spell_buttons`: Lista de (spell, rect) para renderização do menu

## Fluxo de Eventos

```
Jogador em turno
  ↓
Pressiona "S" ou clica botão "Magia"
  ↓
_start_spell_selection()
  - Lista de spells preparados criada
  - spell_selection_active = True
  ↓
Jogador clica em um spell
  ↓
selected_spell = spell escolhido
  - Log mostra "Escolha um alvo..."
  ↓
Jogador clica em um inimigo
  ↓
_cast_spell_on_target(spell, alvo)
  - can_cast_spell() valida
  - Verifica alcance
  - cast_spell() executa
  - Slot consumido
  - has_acted = True
  ↓
Turno do jogador encerrado
```

## Validações Realizadas

1. **Spell preparado**: Verifica se está em prepared_spells
2. **Slots disponíveis**: 
   - Cantrips não usam slots
   - Spells de nível 1+ precisam de slots disponíveis
3. **Alcance**: Calcula Manhattan distance vs spell.range_ft
4. **Alvo vivo**: Só pode alvejar inimigos vivos
5. **Sem aliados**: Não permite alvejar próprio lado (apenas inimigos)

## Interface Visual

### Painel de Seleção (lado esquerdo)
- Título "Selecione uma Magia:"
- Botões para cada spell
- Cada botão mostra: `Nome da Magia (cantrip)` ou `Nome (slot N)`
- Botão destacado quando um spell é selecionado
- Instruções: "ESC para cancelar" ou "Escolha um alvo"

### Botão de Magia
- Localizado ao lado do botão "Terminar Turno"
- Ativado: cor BUTTON, texto branco
- Desativado: cor BUTTON_DISABLED quando já usou ação
- Rótulo: "Magia (S)" com sugestão de tecla
- Apenas aparece se personagem tem spells preparados

### Log de Combate
- Mostra mensagens como:
  - "Gandalf escolhe uma magia para lançar"
  - "Gandalf lança Magic Missile: Acerta Goblin por 8 de dano!"
  - "Alvo fora do alcance da magia..."

## Notas de Implementação

- **Spell slots são consumidos após lançamento bem-sucedido**
- **A ação (action) do turno é consumida quando um spell é lançado**
- **Cantrips podem ser usados múltiplas vezes (não consomem slots)**
- **O range_ft do spell é convertido para tiles dividindo por 5**
- **A distância é calculada usando Manhattan distance (não Euclidiana)**
- **Spells com range 0 (self) só podem alvejar o caster**

## Testes

Execute `python3 -m pytest test_combat_spells.py` para validar:

- ✓ Spells castáveis são retornados corretamente
- ✓ Modo de seleção inicializa corretamente
- ✓ Lançamento bem-sucedido consome slots e causa dano
- ✓ Validação de alcance funciona
- ✓ Cancelamento de seleção limpa estado
- ✓ Personagens sem spells não mostram menu
- ✓ Múltiplos spells podem ser selecionados

## Próximas Melhorias Possíveis

- [ ] Animação visual do spell sendo lançado
- [ ] Som effects para lançamento
- [ ] Preview de alcance quando selecionando spell
- [ ] Suporte a spells com área de efeito
- [ ] Spells de cura/buff para aliados
- [ ] Spells que requerem saving throws do alvo
- [ ] Spells com efeito de concentração
- [ ] HUD mostrando spells restantes durante turno
