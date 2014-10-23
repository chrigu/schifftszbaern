h = 50;

l_outer = 50;
l_inner = 44;
wall = (l_outer-l_inner)/2;

wall_diag = sqrt(2*(wall*wall));

plug_w = 12.1;
plug_h = 11.25;

nupsi_w = 1.5;
nupsi_h = 1.5;
nupsi_d = wall;

nupsi_neg_w = nupsi_w + 0.2;
nupsi_neg_h = nupsi_h + 0.2;
nupsi_neg_d = nupsi_d + 0.2;

nupsi_inset = 4;

module roundedRect(size, radius, $fn=20) {
	x = size[0];
	y = size[1];
	z = size[2];

	linear_extrude(height=z)
	hull() {
		translate([radius, radius, 0])
		circle(r=radius);

		translate([x - radius, radius, 0])
		circle(r=radius);

		translate([x - radius, y - radius, 0])
		circle(r=radius);

		translate([radius, y - radius, 0]) circle(r=radius);
	}
}


module the_cube() {
	rounded_c = 3.3;
	difference(){
		rotate([90,0,0]) roundedRect([l_outer,l_outer,l_outer], 3);
		translate([wall, -(wall+l_inner),wall]) cube(size=[l_inner, l_inner+10, l_inner], center = false);
		translate([nupsi_inset, -wall,wall-nupsi_neg_h]) cube([nupsi_neg_w,100, l_inner+2*nupsi_neg_h]);
		translate([l_outer-(nupsi_inset+nupsi_neg_w), -wall,wall-nupsi_neg_h]) cube([nupsi_neg_w,100, l_inner+2*nupsi_neg_h]);
	}
}


module cloud() {
	union(){
		translate([51,0,0]) cylinder(h=h, r=51);
		translate([138,-13,0]) cylinder(h=h, r=49);
		translate([195,-2,0]) cylinder(h=h, r=41);
		translate([220,2,0]) cylinder(h=h, r=41);
		translate([167,58,0]) cylinder(h=h, r=61);
		translate([83,55,0]) cylinder(h=h, r=44);
		translate([75,-120,0]) rotate(a=[0,0,30]) cube([4,120,h]);
		translate([110,-100,0]) rotate(a=[0,0,30]) cube([4,100,h]);
		translate([170,-120,0]) rotate(a=[0,0,30]) cube([4,120,h]);
		translate([205,-100,0]) rotate(a=[0,0,30]) cube([4,100,h]);
		translate([265,-120,0]) rotate(a=[0,0,30]) cube([4,120,h]);
		}
}

module opener1(){
			difference(){
				union(){
					cube(size=[l_inner*0.7,l_inner*0.7,wall]);
					translate([0,(l_inner)/2,wall]) difference() {
						rotate(a=[0,20,0]) cube([10,10,wall], center=true);
						translate([-40,-20,-20]) cube([40,40,40]);
					}
				}
				translate([0,0,-wall]) cube(size=[l_inner,l_inner,wall]);
			}
}

module backplate() {
	translate([wall,10,0]) difference(){
		union(){
			cube(size=[l_inner,l_inner-0.2,wall]);
			translate([nupsi_inset-wall,-nupsi_h,0]) cube([nupsi_w, l_inner+2*nupsi_h-0.2, nupsi_d]);
			translate([(l_outer-wall)-(nupsi_inset+nupsi_w),-nupsi_h,0]) cube([nupsi_w, l_inner+2*nupsi_h-0.2, nupsi_d]);


		}
		translate([8,-0.3,-20]) cube(size=[plug_w+0.1,plug_h+0.1,wall+100]);
	}
}


translate([0,0,l_outer]) rotate(a=[90,0,0]) difference(){
	the_cube();
	translate([5,-l_inner,24]) rotate(a=[90,0,0]) scale(v=[0.15,0.15,0.15]) cloud();
}

backplate();
