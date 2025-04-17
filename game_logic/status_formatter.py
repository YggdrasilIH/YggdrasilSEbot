def format_status(hero):
  lines = [f"{hero.name} Status:"]
  lines.append(f"  HP: {int(hero.hp)}/{int(hero.max_hp)}")
  lines.append(f"  Energy: {hero.energy}")
  lines.append(f"  Control Immunity: {hero.ctrl_immunity}")
  lines.append(f"  Calamity: {hero.calamity}")
  lines.append(f"  Curse of Decay: {hero.curse_of_decay}")
  if hero.atk_reduction:
      lines.append(f"  ATK Reduction: {hero.atk_reduction*100:.0f}%")
  if hero.armor_reduction:
      lines.append(f"  Armor Reduction: {hero.armor_reduction*100:.0f}%")
  control_effects = []
  if hero.has_silence:
      control_effects.append(f"Silence ({hero.silence_rounds})")
  if hero.has_fear:
      control_effects.append(f"Fear ({hero.fear_rounds})")
  if hero.has_seal_of_light:
      control_effects.append(f"Seal of Light ({hero.seal_rounds})")
  if control_effects:
      lines.append("  Control Effects: " + ", ".join(control_effects))
  lines.append(f"  Immune to: {hero.immune_control_effect}")
  return "\\n".join(lines)