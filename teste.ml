var x : int = 5;
var y : int = 0;

while (x > 0) {
    y = y + x;
    x = x - 1;
}

if (y > 10) {
    print y;
} else {
    print 0;
}