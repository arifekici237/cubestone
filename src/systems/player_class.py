"""Player class definitions: Knight, Ranger, Mage."""
from dataclasses import dataclass


@dataclass
class PlayerClass:
    name:          str
    label:         str    # Turkish display name
    color:         tuple  # (R, G, B) for UI
    icon_color:    tuple  # body color for portrait
    base_hp:       int
    base_atk:      int    # additive damage bonus
    base_spd:      float  # speed multiplier (applied to base 8)
    ability_name:  str
    ability_desc:  str
    ability_cd:    float  # seconds
    ability2_name: str   = ''
    ability2_desc: str   = ''
    ability2_cd:   float = 0.0


CLASSES = {
    'knight': PlayerClass(
        name='knight',   label='Savasci',
        color=(220, 80, 60),  icon_color=(180, 60, 40),
        base_hp=150, base_atk=15, base_spd=1.0,
        ability_name='Kalkan Patlamasi',
        ability_desc='Yakin dusmanlara 3x hasar + geri itme',
        ability_cd=6.0,
        ability2_name='Demir Deri',
        ability2_desc='4 sn %50 hasar azaltma',
        ability2_cd=12.0,
    ),
    'ranger': PlayerClass(
        name='ranger',   label='Okcu',
        color=(80, 200, 80),   icon_color=(50, 160, 50),
        base_hp=100, base_atk=10, base_spd=1.3,
        ability_name='Hizli Adim',
        ability_desc='2.5 sn 2x hiz artisi',
        ability_cd=8.0,
        ability2_name='Keskin Atis',
        ability2_desc='En yakin dusmana 4x hasar',
        ability2_cd=5.0,
    ),
    'mage': PlayerClass(
        name='mage',     label='Buyucu',
        color=(100, 140, 255), icon_color=(70, 100, 220),
        base_hp=80,  base_atk=25, base_spd=0.9,
        ability_name='Buz Dalgasi',
        ability_desc='12 birim icindeki dusmanlari yavaslatir',
        ability_cd=10.0,
        ability2_name='Ates Topu',
        ability2_desc='Ileri firlatilan 3x hasarli ates topu',
        ability2_cd=7.0,
    ),
}
CLASS_ORDER = ['knight', 'ranger', 'mage']
