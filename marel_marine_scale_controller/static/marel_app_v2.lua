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
    DispStr(screen, 3, 1, "    [Prog1]: Prints weight on key press.")
    DispStr(screen, 10, 1, "  Prog 1")
    DispStr(screen, 10, 21, "  Reboot")
    connection_status_display(screen)
  elseif disp == "prog_1" then
    DispStr(screen, 1, 1, "  -- Running program 1 --")
    DispStr(screen, 2, 1, "    ```Prints weight on key press'''")
    DispStr(screen, 3, 1, "    [Print]: Print weight")
    DispStr(screen, 4, 1, "    [Stop]: Stop program 1")
    DispStr(screen, 10, 1, "  Print")
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
  set_display('prog_1', screen)

  while 1 do
    connection_status_display(screen)
    display_weight(screen)
    event, value = NextEvent(0)
    if event == 'softkey' and DispGetScr() == screen then
      if value == 1 then
        send_weight(port, 'p')
        DispStr(screen,9,1, "                >>>> SENT <<<<  ")
        sleep(.5)
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


function run_main()
  screen = 2
  output_port = 5
  set_display('main', screen)

  while 1 do
    display_weight(screen)

    connection_status_display(screen)

    event, value = NextEvent(0)

    if event ==  "softkey" and DispGetScr() == screen then
      if value == 1 then
        print('Starting prog 1')
        run_prog_1(output_port, screen)

      elseif value == 3 then
        print('Restarting Lua Interpreter')
        set_display('reload', screen)
        break

      end
      set_display('main', screen)
    else
      keep_port_alive(output_port)
    end
  end
end

run_main()

print('End of Lua Script')