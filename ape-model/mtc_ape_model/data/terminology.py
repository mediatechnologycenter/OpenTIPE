# Copyright 2022 ETH Zurich, Media Technology Center
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Helper methods for dictionnaries.
"""
import random
from argparse import ArgumentParser
from math import ceil

import stanza
from simalign import SentenceAligner
from torch.cuda import is_available as cuda_is_available
from tqdm import tqdm

from mtc_ape_model.utils.misc import tokenize


class TermFrequencyCounter:

    def __init__(self, lang="fr", use_gpu=True,
                 with_tqdm=False, lemma_comparison=True):

        self.lang = lang
        self.with_tqdm = with_tqdm
        self.lemma_comparison = lemma_comparison

        # Pipeline to determine POS and Lemma
        if self.lemma_comparison:
            try:
                stanza.download(lang)
            except:
                print(f"Could not download stanza for {lang}.")
            self.lemma_processor = stanza.Pipeline(lang=self.lang,
                processors='tokenize, pos, lemma', tokenize_pretokenized=True,
                use_gpu=use_gpu)

    def term_frequency(self, src_with_term, tgt, terminology_term="~"):
        # Get lemma's of alle APE words
        if self.lemma_comparison:
            tgt_infos = self.lemma_processor(tgt).to_dict()
            if tgt_infos != []:
                tgt_toks = [token["lemma"] for token in tgt_infos[0]]
            else:
                tgt_toks = []
        else:
            tgt_toks = tokenize([tgt], self.tgt_lang)[0].split(" ")

        # Get all the words to enforce
        # Tokenize (reverse - tokenization for terminology - split)
        src_toks = src_with_term.strip().split(" ")
        src_tok_to_enf = [term.split(terminology_term)[1:] for term in src_toks]
        src_tok_to_enf = [i for j in src_tok_to_enf for i in j if j != []]

        enforced = [i for i in src_tok_to_enf if i in tgt_toks]
        n_enforced = len(enforced)
        n_src_tok_to_enf = len(src_tok_to_enf)
        # 1 if None -> avoid 0-division / there is nothing to enforce
        return (1 if n_src_tok_to_enf == 0 else n_enforced / n_src_tok_to_enf), \
               n_enforced, n_src_tok_to_enf

    def term_frequency_lines(self, src_with_term_lines, tgt_lines,
                             terminology_term="~", average=True):
        result = []
        for ln in (tqdm(list(zip(src_with_term_lines, tgt_lines)),
                desc='Term frequency') if self.with_tqdm else
                zip(src_with_term_lines, tgt_lines)):
            result.append(self.term_frequency(*ln, terminology_term))

        if average:
            result = ((1 if sum(i[2] for i in result) == 0 else
                       sum(i[1] for i in result) / sum(i[2] for i in result)),
                      sum(i[1] for i in result), sum(i[2] for i in result))
        return result

    def term_frequency_files(self, src_with_term_file, tgt_file, out_file=None,
                             terminology_term="~", average=True):
        with open(src_with_term_file, "r") as src:
            with open(tgt_file, "r") as tgt:
                result = self.term_frequency_lines(src.readlines(),
                    tgt.readlines(), average=average,
                    terminology_term=terminology_term)
                if out_file:
                    with open(out_file, "w") as file:
                        if average:
                            file.write(", ".join([str(i) for i in result]))
                        else:
                            for line in result:
                                file.write(", ".join([str(i) for i in line]))
                else:
                    return result


class TerminologyProcessor:

    def __init__(self, src_lang="de",tgt_lang="en", encode_pos=["NOUN", "VERB"], 
            sentence_annotation_threshold= (0.0, 1.0), use_lemma= True,
            default_dict=None, requires_word_alignment=True):
        """ encodes a pair (SRC, TGT) -> (SRC_encoded, TGT), where:
        certain tokens within source are encoded with the lemmatized version
        of the desired target translation. The tokens that are encoded are
        controlled with the parameters set in this init method. They can be
        drawn from a specic POS distribution, random distribution a mix of both
        or simply from a given dictionnary.

        Parameters
        ----------
        src_lang: str
            Source language
        tgt_lang: str
            Target language
        encode_pos: List[str]
            The POS within SRC for which to encode SRC with the lemmatized
            verion within TGT
        sentence_annotation_threshold: Tuple[float]
            Range of the probability at which a token should be encoded (i.e.
            [1.0, 1.0] always all.)
        use_lemma: bool
            Whether to encode terminology with lemma
        default_dict: Optional[Dict]
            Can be used as default dict for `encode_from_dict`.
        """

        # Inits
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.encode_pos = encode_pos
        self.sentence_annotation_threshold = sentence_annotation_threshold
        self.use_lemma = use_lemma
        self.default_dict = self.get_lemma_mapping(default_dict)

        # Pipeline to determine POS and Lemma
        try:
            stanza.download(tgt_lang)
        except:
            print("Could not download stanza for {tgt_lang}.")
        self.tgt_pos_lemma_processor = stanza.Pipeline(lang=self.tgt_lang,
            processors='tokenize,pos,lemma', tokenize_pretokenized=True)

        try:
            stanza.download(src_lang)
        except:
            print("Could not download stanza for {src_lang}.")
        self.src_pos_lemma_processor = stanza.Pipeline(lang=self.src_lang,
            processors='tokenize,pos,lemma', tokenize_pretokenized=True)

        # Pipeline to align SRC and TGT sentence
        self.requires_word_alignment = requires_word_alignment
        if self.requires_word_alignment:
            self.aligner = SentenceAligner(model="bert", matching_methods = "i",
                device="cuda" if cuda_is_available() else "cpu")

    def get_alignments(self, src_sentence, tgt_sentence):
        """ Word tokenized src and tgt sentence as inputs (several as list). """

        assert(type(src_sentence) == type(tgt_sentence))
        assert(self.requires_word_alignment), "Alignment not initalized, "\
            "please set requires_word_alignment==True in init."

        if type(src_sentence) == str:
            src_sentences = [src_sentence]
            tgt_sentences = [tgt_sentence]
        else:
            src_sentences = src_sentence
            tgt_sentences = tgt_sentence

        # Alignment # "i" == "itermax"
        alignments = []
        for s, t in tqdm(zip(src_sentences, tgt_sentences),
                         total=len(src_sentences), desc='Alignments'):
            alignments.append(self.aligner.get_word_aligns(s, t)["itermax"])

        return alignments

    def get_lemma_mapping(self, term_dict):
        """ Get mapping from source lemma to tgt instead of src to tgt. """
        if not term_dict:
            return None

        # Helper method for lemmas
        def extract_infos(all_info):
            infos = []
            for base_info in all_info._sentences:
                info = [token._words[0] for token in base_info._tokens]
                info = [token for token in info]
                info = [(token._text, token._lemma) for token in info]
                infos.extend(info)
            return infos

        keys = list(term_dict.keys())
        lemmas = [stanza.Document([], text=d) for d in keys]
        lemmas = self.src_pos_lemma_processor(lemmas)
        lemmas = [i[0][1] for i in list(map(extract_infos, lemmas))]
        keys = {k: term_dict[v] for k, v in zip(lemmas, keys)}
        return keys

    def encode_from_dict(self, src_sentence, term_dict=None, encode_token="~",
                         use_default_dict=True):
        """ Word tokenized src and dict terminology mapping. """

        # Lemmas in term_dict
        if not term_dict and use_default_dict:
            term_dict = self.default_dict
        if not term_dict:
            print("Attention, no term_dict, nor a default_dict was specified.")
            return src_sentence
        keys = self.get_lemma_mapping(term_dict=term_dict)

        # Make sure input is always a list
        if type(src_sentence) == str:
            src_sentences = [src_sentence]
        else:
            src_sentences = src_sentence

        # Helper method for lemmas
        def extract_infos(all_info):
            infos = []
            for base_info in all_info._sentences:
                info = [token._words[0] for token in base_info._tokens]
                info = [token for token in info]
                info = [(token._text, token._lemma) for token in info]
                infos.extend(info)
            return infos

        # Lemmas in src_sentence
        doc = [stanza.Document([], text=d) for d in src_sentences]
        src_infos = self.src_pos_lemma_processor(doc)
        src_infos = list(map(extract_infos, src_infos))

        # Encode sentences with dict terms
        result = []
        for i in range(len(src_sentences)):
            encoded_sentence = []
            for j in range(len(src_infos[i])):
                if src_infos[i][j][1] in keys:
                    encoded_sentence.append(src_infos[i][j][0] +
                        encode_token + keys[src_infos[i][j][1]])
                else:
                    encoded_sentence.append(src_infos[i][j][0])
            result.append(" ".join(encoded_sentence))

        return result[0] if type(src_sentence) == str else result

    def encode(self, src_sentence, tgt_sentence, alignments=None,
               tgt_infos=None, src_infos=None, encode_token="~"):
        """ Word tokenized src and tgt sentence as inputs (several as list). """

        assert(type(src_sentence) == type(tgt_sentence))
        assert(self.requires_word_alignment), "Alignment not initalized, "\
            "please set requires_word_alignment==True in init."

        if type(src_sentence) == str:
            src_sentences = [src_sentence]
            tgt_sentences = [tgt_sentence]
        else:
            src_sentences = src_sentence
            tgt_sentences = tgt_sentence

        # Alignment # "i" == "itermax"
        if alignments is None:
            alignments = []
            for s, t in zip(src_sentences, tgt_sentences):
                alignments.append(self.aligner.get_word_aligns(s, t)["itermax"])

        # Filter POS tagging and get lemma
        def extract_infos(all_info):
            infos = []
            for base_info in all_info._sentences:
                info = [token._words[0] for token in base_info._tokens]
                info = [token for token in info]
                info = [(token._upos, token._lemma) for token in info]
                infos.extend(info)
            return infos

        if tgt_infos is None:
            doc = [stanza.Document([], text=d) for d in tgt_sentences]
            tgt_infos = self.tgt_pos_lemma_processor(doc)
            tgt_infos = list(map(extract_infos, tgt_infos))
        assert (all([len(tgt_sentences[i].split(" ")) == len(tgt_infos[i])
                     for i in range(len(tgt_infos))]))

        if src_infos is None:
            doc = [stanza.Document([], text=d) for d in src_sentences]
            src_infos = self.src_pos_lemma_processor(doc)
            src_infos = list(map(extract_infos, src_infos))

        assert (all([len(src_sentences[i].split(" ")) == len(src_infos[i])
                     for i in range(len(src_infos))]))

        def enc(src, tgt, alignment, tgt_info, src_info):

            # Random threshold
            threshold = random.uniform(*self.sentence_annotation_threshold)

            # Get encoded source
            encoded_src = []
            splitted_src = src.split()
            splitted_tgt = tgt.split()

            for i in range(len(splitted_src)):

                # Get lemmas for corresponding src token
                corresponding_tgts = [(tgt_info[j][1] if self.use_lemma
                    else splitted_tgt[j]) for j in
                    range(len(tgt_info)) if (i, j) in alignment and
                    tgt_info[j][0] in self.encode_pos and
                    tgt_info[j][0] == src_info[i][0]]

                # Do not specify order of tgt lemmas by ordering them
                corresponding_tgts.sort()

                # Combine original token with lemmas using encode_token with
                # a certain probability (given by threshold)
                # I.e. <src_token>TOK<lemma>
                # Or if several lemmas <src_token>TOK<lemma1>TOK<lemma2>
                if random.random() > threshold and len(corresponding_tgts) == 1:
                    tok = encode_token.join([splitted_src[i]] +
                                            corresponding_tgts)
                else:
                    tok = splitted_src[i]

                encoded_src.append(tok)

            return " ".join(encoded_src)

        encoded_srcs = list(map(enc, src_sentences, tgt_sentences, alignments,
                                tgt_infos, src_infos))

        return encoded_srcs[0] if type(src_sentence) == str else encoded_srcs

    def encode_lines(self, src_lines, tgt_lines, alignments=None, batch_size=1):
        result = []
        iterations = ceil(len(src_lines) / batch_size)
        data = list(zip(src_lines, tgt_lines))
        for it in tqdm(range(iterations), desc='SRC-dict-terms'):
            batch_src = src_lines[it * batch_size:(it + 1) * batch_size]
            batch_tgt = tgt_lines[it * batch_size:(it + 1) * batch_size]
            if alignments:
                batch_alignments = alignments[it * batch_size:(it + 1) * batch_size]
            else:
                batch_alignments = None
            result.extend(self.encode(batch_src, batch_tgt, batch_alignments))
        return result

    def encode_files(self, src_file, tgt_file, out_file=None, alignments=None,
                     batch_size=1):
        with open(src_file, "r") as src:
            with open(tgt_file, "r") as tgt:
                result = self.encode_lines(src.readlines(),
                                           tgt.readlines(), batch_size=batch_size)
                if out_file:
                    with open(out_file, "w") as file:
                        for line in result:
                            file.write(line)
                else:
                    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--src", type=str)
    parser.add_argument("--pe", type=str)
    parser.add_argument("--src_encoded", type=str)
    parser.add_argument("--tgt_lang", type=str, help="Target language")
    parser.add_argument("--ranom_min", type=float, default=0.6)
    parser.add_argument("--ranom_max", type=float, default=1.0)
    args = parser.parse_args()

    processor = TerminologyProcessor(tgt_lang=args.tgt_lang,
        sentence_annotation_threshold=(args.ranom_min, args.ranom_max))
    processor.encode_files(args.src, args.pe, args.src_encoded)
