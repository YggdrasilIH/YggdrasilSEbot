# game_logic/enables.py

import random

class Enable:
    def apply_end_of_round(self, hero, boss):
        pass

class ControlPurify(Enable):
    def apply_end_of_round(self, hero, boss):
        effects = []
        if hero.has_fear:
            effects.append("fear")
        if hero.has_silence:
            effects.append("silence")
        if hero.has_seal_of_light:
            effects.append("seal_of_light")

        if effects:
            effect_to_remove = random.choice(effects)
            if effect_to_remove == "fear":
                hero.has_fear = False
                hero.fear_rounds = 0
                return f"🧠 {hero.name} purifies **Fear**."
            elif effect_to_remove == "silence":
                hero.has_silence = False
                hero.silence_rounds = 0
                return f"🔕 {hero.name} purifies **Silence**."
            elif effect_to_remove == "seal_of_light":
                hero.has_seal_of_light = False
                hero.seal_rounds = 0
                return f"🌟 {hero.name} purifies **Seal of Light**."
        return None

class AttributeReductionPurify(Enable):
    def apply_end_of_round(self, hero, boss):
        messages = []
        reductions = []
        if hasattr(hero, "atk_reduction") and hero.atk_reduction > 0:
            reductions.append("atk")
        if hasattr(hero, "armor_reduction") and hero.armor_reduction > 0:
            reductions.append("armor")

        if reductions:
            chosen = random.choice(reductions)
            if chosen == "atk":
                messages.append(f"💢 {hero.name} purifies {hero.atk_reduction * 100:.0f}% **ATK Reduction**.")
                hero.atk /= (1 - hero.atk_reduction)
                hero.atk_reduction = 0
            elif chosen == "armor":
                messages.append(f"🛡️ {hero.name} purifies **Armor Reduction**.")
                hero.armor = hero.original_armor
                hero.armor_reduction = 0
        return " ".join(messages) if messages else None

class MarkPurify(Enable):
    def apply_end_of_round(self, hero, boss):
        if hero.curse_of_decay > 0:
            hero.curse_of_decay = 0
            return f"🧬 {hero.name} purifies all **Curse of Decay** stacks."
        return None

class BalancedStrike(Enable):
    def apply_crit_bonus(self, damage, crit):
        if crit:
            bonus = int(damage * 0.15)
            return bonus, 0  # Heal amount, extra damage
        else:
            bonus = int(damage * 0.30)
            return 0, bonus

class UnbendingWill(Enable):
    def __init__(self):
        self.remaining_charges = 4

    def prevent_death(self, hero, damage):
        if self.remaining_charges > 0 and damage >= hero.hp:
            self.remaining_charges -= 1
            return True
        return False
