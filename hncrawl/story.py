class Story:
    def __init__(self, id_=None, rank=None, title=None):
        self.id_ = id_
        self.rank = rank
        self.title = title

    def __repr__(self):
        return "{}. {} ({})".format(self.rank, self.title, self.id_)
