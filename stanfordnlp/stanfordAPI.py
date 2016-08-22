from stanfordnlp import stanfordPClient

class StanfordAPI():

    @staticmethod
    def getLocations(value):
        obj = stanfordPClient.parse_text(value)
        if obj:
            res = []
            for x in obj["sentences"][0]["tokens"]:
                if x["ner"] == "LOCATION":
                    res.append(x["word"])
            if res:
                return res
        return None