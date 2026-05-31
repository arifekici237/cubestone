from ursina import Entity, color, Vec3


class Merchant(Entity):
    """Stationary NPC trader."""

    def __init__(self, position=Vec3(8, 35, 0)):
        super().__init__(position=position)

        # Robe / torso
        Entity(parent=self, model='cube',
               color=color.rgb(80, 50, 130),
               scale=(0.70, 0.90, 0.50))

        # Head
        Entity(parent=self, model='sphere',
               color=color.rgb(220, 180, 120),
               scale=(0.52, 0.52, 0.52),
               position=(0, 0.71, 0))

        # Hat brim
        Entity(parent=self, model='cube',
               color=color.rgb(30, 90, 30),
               scale=(0.72, 0.08, 0.72),
               position=(0, 1.01, 0))

        # Hat top
        Entity(parent=self, model='cube',
               color=color.rgb(30, 90, 30),
               scale=(0.44, 0.30, 0.44),
               position=(0, 1.21, 0))

        # Arms
        for sx in (-0.55, 0.55):
            Entity(parent=self, model='cube',
                   color=color.rgb(80, 50, 130),
                   scale=(0.20, 0.70, 0.22),
                   position=(sx, 0, 0))
