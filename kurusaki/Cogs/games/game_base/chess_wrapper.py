import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame(
    # negative = black, positive = white
    # 0 = empty, 1 = pawn, 2 = knight, 3 = bishop, 4 = rook, 5 = queen, 6 = king
    {
        "a": [0,0,0,0,0,0,0,0],
        "b": [0,0,0,0,0,0,0,0],
        "c": [0,0,0,0,0,0,0,0],
        "d": [0,0,0,0,0,0,0,0],
        "e": [0,0,0,0,0,0,0,0],
        "f": [0,0,0,0,0,0,0,0],
        "g": [0,0,0,0,0,0,0,0],
        "h": [0,0,0,0,0,0,0,0]
    }
)


# bishop: a1,b2,c3,d4,e5,f6,g7,h8
# bishop: b1,c2,d3,e4,f5,g6,h7
# bishop: a2,b3,c4,d5,e6,f7,g8
# bishop: g1,h2,f2,e3,d4,c5,b6,a7
df.plot()
plt.show()