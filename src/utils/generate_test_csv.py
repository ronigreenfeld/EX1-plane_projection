"""Generates sample test CSV files containing cutting planes across 3D volumes."""

import os


def generate_mri_planes_csv(output_path: str = "data/real/mri_planes.csv", num_slices: int = 60) -> str:
    """Generates an axial slice sequence through MRHead_1.nrrd (shape 256x256x130).

    Contains a sequence of horizontal axial slices sweeping along the z-axis,
    mixing both isosceles triangles (9 coords) and isosceles trapezoids (12 coords).
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Cutting planes for MRHead_1.nrrd (axial sweep)\n")

        # Axial sweep: z ranges from 15 to 115 across 60 frames
        z_start = 15.0
        z_end = 115.0
        z_step = (z_end - z_start) / float(num_slices)

        for i in range(num_slices):
            z = z_start + i * z_step

            if i % 2 == 0:
                # Isosceles Triangle (9 coordinates):
                # Apex at (128, 10, z), base endpoints at (10, 245, z) and (246, 245, z)
                # dist(a, b) = sqrt((-118)^2 + 235^2)
                # dist(a, c) = sqrt(118^2 + 235^2) == dist(a,b) exactly!
                ax, ay, az = 128.0, 10.0, z
                bx, by, bz = 10.0, 245.0, z
                cx, cy, cz = 246.0, 245.0, z
                f.write(f"{ax:.2f}, {ay:.2f}, {az:.2f}, {bx:.2f}, {by:.2f}, {bz:.2f}, {cx:.2f}, {cy:.2f}, {cz:.2f}\n")
            else:
                # Isosceles Trapezoid (12 coordinates):
                # Top base: (90, 20, z) to (166, 20, z) -> width = 76
                # Bottom base: (20, 240, z) to (236, 240, z) -> width = 216
                # Legs: dist((90,20), (20,240)) = sqrt((-70)^2 + 220^2)
                #       dist((166,20), (236,240)) = sqrt(70^2 + 220^2) -> Equal!
                a1x, a1y, a1z = 90.0, 20.0, z
                a2x, a2y, a2z = 166.0, 20.0, z
                bx, by, bz = 20.0, 240.0, z
                cx, cy, cz = 236.0, 240.0, z
                f.write(f"{a1x:.2f}, {a1y:.2f}, {a1z:.2f}, {a2x:.2f}, {a2y:.2f}, {a2z:.2f}, {bx:.2f}, {by:.2f}, {bz:.2f}, {cx:.2f}, {cy:.2f}, {cz:.2f}\n")

    return output_path


if __name__ == "__main__":
    path = generate_mri_planes_csv()
    print(f"Generated sample CSV at: {path}")
