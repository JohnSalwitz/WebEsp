puts "Checking Pin Value"
set pinval [digitalread 1]
puts $pinval
if {$pinval == 0} {
    puts "pin is low"
    log
}