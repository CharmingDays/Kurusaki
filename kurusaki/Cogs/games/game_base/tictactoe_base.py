

class TicTacToe():
    def __init__(self) -> None:
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.winner = None


    def is_valid_move(self,location:str):
        """
        Check if the move is valid
        """

        if len(location) != 2:
            return False

        for index in location:
            #validate location
            if not index.isdigit() or int(index) > 2 or int(index) < 0:
                return False
        
        #validate if the location is already taken
        if self.board[int(location[0])][int(location[1])] != "":
            return False
        
        return True



    def check_winner(self):
        """
        Check if there is a winner
        """
        #check row
        for row in self.board:
            if row[0] == row[1] == row[2] and row[0] != "":
                self.winner = row[0]
                return self.winner

        #check column
        for i in range(3):
            if self.board[0][i] == self.board[1][i] == self.board[2][i] and self.board[0][i] != "":
                self.winner = self.board[0][i]
                return self.winner

        #check diagonal
        if self.board[0][0] == self.board[1][1] == self.board[2][2] and self.board[0][0] != "":
            self.winner = self.board[0][0]
            return self.winner

        if self.board[0][2] == self.board[1][1] == self.board[2][0] and self.board[0][2] != "":
            self.winner = self.board[0][2]
            return self.winner

        return None



    def mark_board(self,mark,location:str):
        """
        Mark the board with the player's mark X or O given array index
        EX: 01 02 11 03 33
        """
        if self.is_valid_move(location):
            self.board[int(location[0])][int(location[1])] = mark.upper()
            return self.check_winner()

        else:
            return ValueError("Invalid move, location must be between 0-2, not taken yet, and must be in the format of '01' '02'")

    def draw_text_board(self):
        """
        Draw the board in text format
        """
        board = ""
        for row in self.board:
            for index,cell in enumerate(row):
                if index == 2:
                    board += f"{cell}"
                elif cell == "":
                    board += " |"
                else:
                    board += f"{cell}|"

            board += "\n"
        return board
        
