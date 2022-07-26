def get_protocol_messages(protocol_name, role):
    with open("./protocols/{}/{}.txt".format(protocol_name, role)) as f:
        msgs = f.read().splitlines()
    res = []
    for msg in msgs:
        res.append(get_protocol_msg_description(msg))
    res_dic = {}
    for msg in res:
        if msg[0] not in res_dic:
            res_dic[msg[0]] = []
        res_dic[msg[0]].append([msg[1], msg[2]])
    #print("dic: ", res_dic)
    return res_dic

def get_protocol_msg_description(msg):
    vals = msg.split(" ")
    activator = vals[0]
    msg = vals[1]
    dst = vals[2]
    return [activator, dst, msg]

def get_protocols_first_message(protocol_name):
    with open("./protocols/{}/initiate.txt".format(protocol_name)) as f:
        msg = f.readline()[:-1] # to remove the '\n' character at the end
    vals = msg.split(" ")
    src = vals[0]
    dst = vals[1]
    msg = vals[2]
    return (src, dst, msg)



