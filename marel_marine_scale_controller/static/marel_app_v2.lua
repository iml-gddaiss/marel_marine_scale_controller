print('Starting Lua Script')

function send_weight(port, prefix)
  --[It could check if the comm_port is connect (maybe) before writing to it.]
  --[Check units.]
  weight, stability, zero, net = GetWeight()
  --weight = ScaleTrim(weight)
  weight, dev_range, dev_target, lower_lim, upper_lim = Pack(weight)

  if CommActive(port) == 1 then
    CommStr(port,'%' .. prefix ..',' .. weight .. '#\n')
  end

  print('weight', weight, 'zero', zero)
end


function keep_port_alive(port)
  --[It could check if the comm_port is connect (maybe) before writing to it.]
  CommStr(port, '%#\n') -- Keep alive
  print('') -- Keep alive
end


function connection_status_display(screen)
  if CommActive(output_port) == 1 then
     DispStr(screen, 1, 27, "   [Connected]")
  else
    DispStr(screen, 1, 27, "[Disconnected]")
  end

end


function set_app_display(disp, screen)
  DispClrScr(screen)
  if disp == "main" then
    DispStr(screen, 1, 1, "  Programs")
    DispStr(screen, 2, 1, "  --------")
    DispStr(screen, 3, 1, "    [Prog1]: Prints weight on key press.")
    DispStr(screen, 6, 1, "    [Reboot]: Restart Lua interpreter.")
    DispStr(screen, 10, 1, "  Prog 1")
    DispStr(screen, 10, 21, "  Reboot")
    connection_status_display(screen)
  elseif disp == "prog_1" then
    DispStr(screen, 1, 1, "  -- Running program 1 --")
    DispStr(screen, 2, 1, "- The weight value is continuously sent.")
    DispStr(screen, 3, 1, "- Press the [Print] button, on the main")
    DispStr(screen, 4, 1, "- page to send a print command.")
    DispStr(screen, 5, 1, "- Press the [Stop] button to stop")
    DispStr(screen, 6, 1, " the program.")
    DispStr(screen, 10, 11, "   Stop")
    connection_status_display(screen)
  elseif disp == "reload" then
    DispStr(screen, 1, 1, "  -- Restarting Lua Interpreter --")
  end


end

function run_prog_1(port, screen)
  scale_screen = 1
  print('Launching prog 1')
  set_app_display('prog_1', screen)
  DispStr(scale_screen, 10, 1, "  Print")
  DispStr(scale_screen, 1, 1, "  [Running program 1]")

  while 1 do
    connection_status_display(screen)
    event, value = NextEvent(0)
    if event == 'softkey' then
      if value == 1 and DispGetScr() == scale_screen then
        send_weight(port, 'p')
        DispStr(scale_screen, 10, 1, "  >>>>>")
        sleep(.5) --[this here is to prevent double press of the send button]
        DispStr(scale_screen, 10, 1, "  Print")
        while NextEvent(0) == "softkey" do
            sleep(.01)
          end
      elseif value == 2 then
        print('Exiting loop')
        break
      end
    else
      send_weight(port, 'w')
      --keep_port_alive(comm_port)
    end
  end
  print("Exiting program 1")
end


function run_main()
  app_screen = 2
  output_port = 5
  set_app_display('main', app_screen)

  while 1 do
    connection_status_display(app_screen)

    event, value = NextEvent(0)

    if event ==  "softkey" and DispGetScr() == app_screen then
      if value == 1 then
        print('Starting prog 1')
        run_prog_1(output_port, app_screen)

      elseif value == 3 then
        print('Restarting Lua Interpreter')
        set_app_display('reload', app_screen)
        break

      end
      set_app_display('main', app_screen)
    else
      keep_port_alive(output_port)
    end
  end
end

run_main()

print('End of Lua Script')