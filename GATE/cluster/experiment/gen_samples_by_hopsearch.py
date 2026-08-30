import argparse, os, subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nsg_path',   required=True)
    parser.add_argument('--base_path',  required=True)
    parser.add_argument('--hub_path',   required=True)
    parser.add_argument('--hub_txt',    required=True)
    parser.add_argument('--query_path', required=True)
    parser.add_argument('--output_dir', required=True)
    parser.add_argument('--search_L',   type=int, default=100)
    parser.add_argument('--t_pos',      type=int, default=3)
    parser.add_argument('--neg_size',   type=int, default=64)
    parser.add_argument('--workers',    type=int, default=1)
    parser.add_argument('--batch_q',    type=int, default=2000)
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    cpp_binary = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../build/tests/test_gate_generate_samples')
    if not os.path.exists(cpp_binary):
        cpp_binary = '/mnt/new/New/ACSG/GATE/build/tests/test_gate_generate_samples'
    
    cmd = [
        cpp_binary,
        args.base_path,
        args.query_path,
        args.nsg_path,
        args.hub_txt,
        str(args.search_L),
        "100", # search_K
        args.output_dir
    ]
    
    print(f'[GenSamples] Running C++ hop-search: {" ".join(cmd)}')
    subprocess.run(cmd, check=True)
    
    print(f'[GenSamples] Done. Samples saved to {args.output_dir}')

if __name__ == '__main__':
    main()
