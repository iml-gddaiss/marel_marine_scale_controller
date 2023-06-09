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


function set_display(disp, screen)
  DispClrScr(screen)
  if disp == "main" then
    DispStr(screen, 1, 1, "  Programs")
    DispStr(screen, 2, 1, "  --------")
    DispStr(screen, 3, 1, "    [Prog1]: Sends weight on key press.")
    DispStr(screen, 4, 1, "    [Prog2]: Always sends weight.")
    DispStr(screen, 10, 1, "  Prog 1")
    DispStr(screen, 10, 11, "  Prog 2")
    DispStr(screen, 10, 21, "  Reboot")
    connection_status_display(screen)
  elseif disp == "prog_1" then
    DispStr(screen, 1, 1, "  -- Running program 1 --")
    DispStr(screen, 2, 1, "    ```Sends weight on key press.'''")
    DispStr(screen, 3, 1, "    [send]: Send weight.")
    DispStr(screen, 4, 1, "    [stop]: Stop program 1")
    DispStr(screen, 10, 1, "   Send")
    DispStr(screen, 10, 11, "   Stop")
    connection_status_display(screen)
  elseif disp == "prog_2" then
    DispStr(screen, 1, 1, "  -- Running program 2 --")
    DispStr(screen, 2, 1, "    ```Always sends weight.'''")
    DispStr(screen, 3, 1, "     [stop]: Stop program 2")
    DispStr(screen, 10, 11, "   Stop")
    connection_status_display(screen)
  elseif disp == "reload" then
    DispStr(screen, 1, 1, "  -- Restarting Lua Interpreter --")
  end


end

function display_weight(screen)
  weight, stability, zero, net = GetWeight()
  weight, dev_range, dev_target, lower_lim, upper_lim = Pack(weight)
  DispStr(screen, 6,12, "+-------------------------+")
  DispStr(screen, 7,12, "| Weight:  ".. DoubleDigits(weight) .. "  |")
  DispStr(screen, 8,12, "+-------------------------+")
  --DispStr(screen, 7, 2, "Current Display " .. DispGetScr())
end


function run_prog_1(port, screen)
  print('Launching prog 1')
  set_app_display('prog_1', screen)

  while 1 do
    connection_status_display(screen)
    display_weight(screen)
    event, value = NextEvent(0)
    if event == 'softkey' and DispGetScr() == screen then
      if value == 1 then
        send_weight(port, 'p')
        DispStr(screen,9,1, "  >>>>>>>>>>>>>>> SENT <<<<<<<<<<<<<<<  ")
        sleep(1)
        DispStr(screen,9,1, "                                        ")
        --[this here is to prevent double press of the send button]
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


function run_prog_2(port, screen)
  print('Launching prog 2')

  set_app_display('prog_2', screen)

  while 1 do
    connection_status_display(screen)
    display_weight(screen)
    send_weight(port, 'w')
    event, value = NextEvent(0)
    if event == 'softkey' and DispGetScr() == screen then
      if value == 2 then
        print('Exiting loop')
        break
      end
    end
  end
  print("Exiting program 2")
end


function run_main()
  app_screen = 2
  output_port = 5
  set_app_display('main', app_screen)

  while 1 do
    display_weight(app_screen)

    connection_status_display(app_screen)

    event, value = NextEvent(0)

    if event ==  "softkey" and DispGetScr() == app_screen then
      if value == 1 then
        print('Starting prog 1')
        run_prog_1(output_port, app_screen)

      elseif value == 2 then
        print('Starting prog 2')
        run_prog_2(output_port, app_screen)

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