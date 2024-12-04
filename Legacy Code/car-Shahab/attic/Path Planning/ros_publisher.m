rosshutdown
rosinit
rostopic list
chatpub = rospublisher('/chatter','std_msgs/String');
msg = rosmessage(chatpub);
msg.Data = 'test phrase';
send(chatpub, msg);
rostopic echo '/chatter';