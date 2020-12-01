#!/usr/bin/env ruby
# Version 0.2

MAX_NETWORK_PING = 4
TIMEOUT = 1

GREEN = 92
RED = 31
CYAN = 36

IP_ADDRESS = '1.1.1.1'

def down?(host, max_ping, timeout = TIMEOUT)
  !up?(host, max_ping, timeout)
end

def up?(host, max_ping, timeout = TIMEOUT)
  ping_result = `ping -c #{max_ping} #{host}`
  success = ping_result.split(" time=")

  success.count >= max_ping
end

def style(str, style_code)
  "\e[#{style_code}m#{str}\e[0m"
end


start_time = Time.now
while true do
  if down?(IP_ADDRESS, MAX_NETWORK_PING, TIMEOUT)
    puts "Final Time: #{Time.now - start_time}"
    break
  end

  sleep(1)
  puts "Diff Time: #{Time.now - start_time}"
end
