// polyfills for IE<9
(function(fn) {
	if (!fn.map) {
		fn.map = function(f/*, thisArg */) {
			if (this === void 0 || this === null)
				throw new TypeError();

			var t = Object(this);
			var len = t.length >>> 0;
			if (typeof f !== "function")
				throw new TypeError();

			var res = new Array(len);
			var thisArg = arguments.length >= 2 ? arguments[1] : void 0;
			for (var i = 0; i < len; i++) {
				if (i in t)
					res[i] = f.call(thisArg, t[i], i, t);
			}

			return res;
		}
	}
	if (!fn.forEach) {
		fn.forEach = function (f/*, thisArg */) {
			if (this === void 0 || this === null)
				throw new TypeError();

			var t = Object(this);
			var len = t.length >>> 0;
			if (typeof f !== "function")
				throw new TypeError();

			var thisArg = arguments.length >= 2 ? arguments[1] : void 0;
			for (var i = 0; i < len; i++) {
				if (i in t)
					f.call(thisArg, t[i], i, t);
			}
		}
	}
})(Array.prototype);

var exterior = {

	/**
	 * the actual words finally used to query (set by last search call)
	 */
	queryWords: [],

	search: function(query) {
		var words = exterior.tokenizeString(query);
		var result = {};

		exterior.queryWords = words.map(function(i) { return i.t; });

		// do not search when no words given
		if (!words.length) {
			return result;
		}

//		result = exterior.searchForWords(words);
//		if ($.isEmptyObject(result)) {
			words = exterior.completeWords(words);
			exterior.queryWords = words.map(function(i) { return i.t; });
			result = exterior.searchForWords(words);
//		}

		var res = [];
		for (var i in result) {
			res.push(result[i]);
		}
		res.sort(function(a,b) { return b.weight - a.weight; });
        
        var sub_res = exterior.filterFalsePositives(res, words);

		return sub_res;
	},

	searchForWords: function(words) {
		var result = {};
		words.forEach(function(word) {
			if (exterior.index[word.t]) {
				exterior.index[word.t].forEach(function(file) {
					if (result[file.f]) {
						result[file.f].weight *= file.w * word.w;
					} else {
						result[file.f] = {
                            identifier: file.f,
							file: exterior.files[file.f],
							weight: file.w * word.w
						};
					}
				});
			}
		});
		return result;
	},

    filterFalsePositives: function(results, words) {
        var new_results = [];
        for (var result in results) {
            var next = results[result];
            var all = true;
            words.forEach(function(word) {
                if (exterior.index[word.t]){
                    var in_next = false;
                    var word_index = exterior.index[word.t];
                    for (var file in word_index) {
                        if (word_index[file].f ==  next.identifier){
                            in_next = true;
                            break;
                        }
                    }
                    if (!in_next){
                        all = false;
                        return;
                    }
                }
            });
            if(all){
                new_results.push(results[result]);
            }
        };
        return new_results;
    },

	completeWords: function(words) {
		var result = [];

		words.forEach(function(word) {
			if (!exterior.index[word.t] && word.t.length > 2) {
				// complete words that are not in the index
				for(var w in exterior.index) {
					if (w.substr(0, word.t.length) === word.t) {
						result.push({t: w, w: 1});
					}
				}
			} else {
				// keep existing words
				result.push(word);
			}
		});
		return result;
	},

	tokenizeString: function(string)
	{
		if (console) {
			console.log('Error: tokenizeString should have been overwritten by index JS file.')
		}
		return [{t: string, w: 1}];
	}
};
