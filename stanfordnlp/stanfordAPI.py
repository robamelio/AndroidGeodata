from stanfordnlp import stanfordPClient

class StanfordAPI():

    @staticmethod
    def getLocations(value):
        obj = stanfordPClient.parse_text(value)
        if obj:
            res = []
            for y in obj["sentences"]:
                for x in y["tokens"]:
                    if x["ner"] == "LOCATION":
                        res.append(x["word"])
            if res:
                return res
        return None