#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <time.h>
#include <string.h>

// Frame structure constants
#define USB_SOF 0x55555555
#define USB_EOF 0xAAAAAAAA
#define N_FRAME_DATA 1250
#define FRAME_TOTAL_INTS 1253  // SOF + timestamp + 1250 data + EOF
#define FRAME_INTERVAL 100 // 100 ms
// #define BUFF_SIZE 8192

typedef enum
{
    STATE_FIND_SOF,
    STATE_FIND_EOF,
} STATE_t;

struct my_args_t
{
    char *tty_dev;
    char *o_csv_file;
};

// Global file pointer for signal handler
FILE *fcsv = NULL;

#include <signal.h>

void handle_signal(int sig) {
    if (fcsv) {
        fflush(fcsv);
        fclose(fcsv);
        fcsv = NULL;
    }
    //fprintf(stderr, "\nTerminated by signal %d. Output file flushed and closed.\n", sig);
    exit(128 + sig);
}

void parse_arg(int argc, char* argv[], struct my_args_t *my_args)
{
    // set default arguments
    my_args->tty_dev = "/dev/ttyACM0";
    my_args->o_csv_file = "vibration_data.csv";

    for(int i = 1; i < argc; i++)
    {
        if(strcmp(argv[i], "-p") == 0 && ++i < argc)
        {
            my_args->tty_dev = argv[i];
        }
        else if(strcmp(argv[i], "-o") == 0 && ++i < argc)
        {
            my_args->o_csv_file = argv[i];
        }
    }
    fprintf(stdout, "Read port: %s\nOutput CSV file: %s\n", my_args->tty_dev, my_args->o_csv_file);
}

int set_tty(char* tty_dev)
{
    int tty_fd = open(tty_dev, O_RDONLY | O_NOCTTY);
    if(tty_fd < 0)
    {
        fprintf(stderr, "Fail to open %s\n", tty_dev);
        return -1;
    }

    struct termios tty;
    tcgetattr(tty_fd, &tty);
    tty.c_cflag |= (CLOCAL | CREAD);
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8; // 8 bits
    tty.c_cflag &= ~PARENB; // no parity
    tty.c_cflag &= ~CSTOPB; // 1 stop bit
    tty.c_cflag &= ~CRTSCTS; // no flow control
    tty.c_lflag = 0; // raw mode
    tty.c_oflag = 0;
    tty.c_iflag = 0;
    tcsetattr(tty_fd, TCSANOW, &tty);

    // Flush input buffer to clear any stale data
    tcflush(tty_fd, TCIFLUSH);

    return tty_fd;
}

FILE* set_output_file(char *o_csv_file)
{
    FILE *fp = fopen(o_csv_file, "w");
    return fp;
}

int main(int argc, char* argv[])
{
    struct my_args_t my_args;
    parse_arg(argc, argv, &my_args);

    // Register signal handlers
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    int tty_fd = set_tty(my_args.tty_dev);
    if(tty_fd < 0)
    {
        fprintf(stderr, "Failed to set up tty device, please check if you've connect the USB device and give the right port\n");
        return EXIT_FAILURE;
    }

    fcsv = set_output_file(my_args.o_csv_file);
    if (!fcsv)
    {
        fprintf(stderr, "Failed to set up output file\n");
        close(tty_fd);
        return EXIT_FAILURE;
    }

    struct timespec delay_time = 
    {
        .tv_sec = 0,
        .tv_nsec = 1000000 // 1 ms
    };

    int32_t *frame_buff = (int32_t*)calloc(FRAME_TOTAL_INTS, sizeof(int32_t));
    if(!frame_buff)
    {
        fprintf(stderr, "USB buffer allocation failed\n");
        close(tty_fd);
    if (fcsv) { fclose(fcsv); fcsv = NULL; }
        return EXIT_FAILURE;
    }

    STATE_t state = STATE_FIND_SOF;
    int32_t *read_ptr = frame_buff; // Pointer to the current position in the frame buffer

    fprintf(fcsv, "timestamp,data\n"); // CSV header
    while(1)
    {
        // Number of int read from the tty, frame buffer space remaining: total - (read_ptr - frame_buff)
        int n = read(tty_fd, read_ptr, (FRAME_TOTAL_INTS - (read_ptr - frame_buff))*sizeof(int32_t))/4;
        if(n < 0) // Error reading from tty
        {
            fprintf(stderr, "Error reading from tty\n");
            free(frame_buff);
            close(tty_fd);
            if (fcsv) { fclose(fcsv); fcsv = NULL; }
            return EXIT_FAILURE;
        }
        // fprintf(stdout, "%d of data read\n", n);
        if(n == 0) // No data read
        {
            nanosleep(&delay_time, NULL); // Sleep 
            continue;
        }
        if(state == STATE_FIND_SOF)
        {
            if(*read_ptr != USB_SOF)
                continue; // Not the start of frame, wait for next data
            state = STATE_FIND_EOF; // Move to next state after finding SOF
            // fprintf(stdout, "Start of frame detected\n");
        }
        if(state == STATE_FIND_EOF)
        {
            read_ptr += n-1; // Move to the end of the current read
            if(*read_ptr != (int32_t)USB_EOF)
            {
                if(read_ptr - frame_buff >= FRAME_TOTAL_INTS)
                {
                    fprintf(stderr, "Error length of frame!\n%d ints expected!\n", FRAME_TOTAL_INTS);
                    read_ptr = frame_buff; // Reset read pointer
                    state = STATE_FIND_SOF; // Reset state to find SOF again
                    continue; 
                }
                read_ptr++; // Move to the next position for the next read
                nanosleep(&delay_time, NULL); // Sleep 
                continue;
            }

            if ((read_ptr - frame_buff + 1) != FRAME_TOTAL_INTS) {
                fprintf(stderr, "Warning: Frame size mismatch at %u! Read %ld ints, expected %d ints.\n", (uint32_t)frame_buff[1],
                        read_ptr - frame_buff + 1, FRAME_TOTAL_INTS);
            }

            static uint32_t last_frame_timestamp = 0;
            if (last_frame_timestamp != 0) 
            {
                uint32_t interval = (uint32_t)frame_buff[1] - last_frame_timestamp;
                if (interval != FRAME_INTERVAL) {
                    fprintf(stderr, "Warning: Frame interval mismatch! Expected %d ms, got %d ms.\n", FRAME_INTERVAL, interval);
                }
            }
            last_frame_timestamp = (uint32_t)frame_buff[1];
            // Print timestamp
            // fprintf(stdout, "%d\n", last_frame_timestamp);
            // Print data
            uint64_t data_timestamp = (uint32_t)frame_buff[1] * 1000; // in microseconds
            for(int i = 2; i < FRAME_TOTAL_INTS - 1; i++)
            {
                fprintf(fcsv, "%lu,%d\n", data_timestamp, frame_buff[i]);
                data_timestamp += (FRAME_INTERVAL * 1000) / (FRAME_TOTAL_INTS - 3); // Increment timestamp by frame interval
            }

            // Reset read pointer and state for the next frame
            read_ptr = frame_buff;
            state = STATE_FIND_SOF;
        }
    }

    free(frame_buff);
    close(tty_fd);
    if (fcsv) { fclose(fcsv); fcsv = NULL; }
    return EXIT_SUCCESS;
}
