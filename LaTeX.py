#-----------------------------------------------------------------------------

def escapeLaTeX(text):

    if text is None:
        return None

    inQuote = False
    ret = ''
    for c in text:
        if c == '"':
            if inQuote:
                ret += '\'\''
            else:
                ret += '``'
            inQuote = not inQuote;
        elif c == u'&':
            ret += '\&'
        elif c == u'\u202f':
            ret += '\\,'
        elif c == u'%':
            ret += '\\%'
        elif c == u'\\':
            ret += '\\textbackslash{}'
        elif c == u'^':
            ret += '\\textasciicircum{}'
        elif c == u'~':
            ret += '\\textasciitilde{}'
        elif c == u'$':
            ret += '\\$'
        elif c == u'#':
            ret += '\\#'
        elif c == u'_':
            ret += '\\_'
        elif c == u'{':
            ret += '\\{'
        elif c == u'}':
            ret += '\\}'
        else:
            ret += c
    return ret

#-----------------------------------------------------------------------------
